import random

from celery import shared_task
from django.utils import timezone

from boostress.utils import time_difference_min, get_qty
from campaign_manager.models import Order, EngagementConfig, ServiceTask
from delivery_cloud.agent_api import AgentApi
from delivery_cloud.models import Agent, AgentOpResult, OP_SEND, OP_FWD, Endpoint, AgentResource, AgentService
from provider_api.common import APIFactory


@shared_task(bind=True)
def deploy_resource(self, last_message_hrs=4, probability_threshold=3):
    agent = Agent.objects.first()
    endpoints = AgentOpResult.objects.get_available_endpoints(last_message_hrs)

    if not endpoints:
        return {"task": "deploy_resource", "detail": "all endpoints are busy, exiting"}

    endpoint = random.choice(endpoints)

    probability = random.randint(1, 10)
    if probability < probability_threshold:
        op_type = OP_FWD
    else:
        op_type = OP_SEND

    last_deployments = AgentOpResult.objects.exclude(endpoint=endpoint).exclude(is_fwd=True).filter(
        created__lte=timezone.now() - timezone.timedelta(days=2)
    ).order_by('-id')[0:10]
    if op_type == OP_FWD and not last_deployments:
        return {"endpoint": endpoint.name, "operation": op_type, "detail": "Nothing to forward, exiting"}

    if op_type == OP_SEND:
        other_endpoints = Endpoint.objects.exclude(id=endpoint.id)
        another_endpoint = None
        if len(other_endpoints) > 0:
            another_endpoint = random.choice(other_endpoints)
        out = create_resource(agent, endpoint, another_endpoint)
        return {"endpoint": endpoint.name, "operation": op_type, "out": out}

    elif op_type == OP_FWD:
        op_resource = random.choice(last_deployments)
        out = fwd_resource(agent, endpoint, op_resource)
        return {"endpoint": endpoint.name, "operation": op_type, "resource": op_resource.ref_url, "out": out}

    return None


def create_resource(agent, endpoint, another_endpoint=None):
    resource = random.choice(AgentResource.objects.filter(is_active=True).order_by('-id')[:10])
    op_id = 0
    use_reference = False
    if another_endpoint and random.randint(1, 10) < 3:
        op_id = AgentApi.create(agent.api_url, agent.token, endpoint.ext_id, resource.url, another_endpoint.label, resource.resource_type, resource.caption)
        use_reference = True
    else:
        op_id = AgentApi.create(agent.api_url, agent.token, endpoint.ext_id, resource.url, None, resource.resource_type, resource.caption)

    if op_id == 0:
        return {"status": "error", "details": "CREATE: op_id is 0", "endpoint": endpoint.name, "operation": "create"}

    endpoint.message_qty = op_id
    endpoint.save()
    out = AgentOpResult.objects.create(endpoint=endpoint, ref_id=op_id,
                                       ref_url="{}/{}/{}".format(agent.endpoint_url, endpoint.label,
                                                                 endpoint.message_qty))

    Order.objects.get_deployment_order_by_id(out.id, out.endpoint, out.ref_url)
    return {"status": "success", "created": out.ref_url}


def fwd_resource(agent, endpoint, op_resource):
    op_id = AgentApi.forward(agent.api_url, agent.token, endpoint.ext_id, op_resource.endpoint.ext_id,
                             op_resource.ref_id)
    if op_id == 0:
        return {"status": "error", "details": "FWD: op_id is 0", "endpoint": endpoint.name, "operation": "create"}

    endpoint.message_qty = op_id
    endpoint.save()
    out = AgentOpResult.objects.create(endpoint=endpoint, ref_id=op_id,
                                       ref_url="{}/{}/{}".format(agent.endpoint_url, endpoint.label,
                                                                 endpoint.message_qty),
                                       is_fwd=True)
    fulfill_delivery.apply_async((out.id, "{}/{}".format(agent.endpoint_url, op_resource.endpoint.label)),
                                 countdown=60 * 5)
    return {"status": "success", "created": out.ref_url}


@shared_task(bind=True)
def manage_delivery(self, last_message_hrs=2):
    active_deployments = AgentOpResult.objects.get_active_deployments(last_message_hrs)

    deployment_refs = []
    for deployment in active_deployments:
        deployment_refs.append(deployment.ref_url)
        fulfill_delivery.delay(deployment.id)

    return {"task": "manage_delivery", "processing": deployment_refs}


@shared_task(bind=True)
def fulfill_delivery(self, deployment_id, ref=""):
    is_ref = bool(ref)
    deployment = AgentOpResult.objects.get(pk=deployment_id)
    active_order, is_created = Order.objects.get_deployment_order_by_id(deployment_id, deployment.endpoint, deployment.ref_url)

    result_list = []

    for agent_service in AgentService.objects.filter(is_ref=is_ref):
        if timezone.now() > active_order.get_last_completed_task_time(deployment.ref_url,
                                                                      agent_service.service) \
                and timezone.timedelta(
            minutes=agent_service.service.start_after) < timezone.now() - deployment.created < timezone.timedelta(
            minutes=agent_service.service.end_after):
            engagement_min, engagement_max = EngagementConfig.objects.get_config(link_type=active_order.link_type,
                                                                                 service_type=agent_service.service.service_type,
                                                                                 platform_name=active_order.platform.name)
            time_difference = time_difference_min(deployment.created)

            qty = get_qty(time_difference, active_order.total_followers, agent_service.service.min,
                          agent_service.service.max, engagement_min,
                          engagement_max, False)

            if qty < agent_service.service.min:
                result_list.append({
                    "result": "Order {}, qty is {}, attempted the service {}, the QTY is less than {}".format(
                        active_order.name,
                        qty,
                        agent_service.service.service_id,
                        agent_service.service.min)})
                continue

            if not is_ref:
                link = deployment.ref_url
            else:
                link = ref

            try:
                provider_api = APIFactory.get_api(agent_service.service.provider.api_type)
                ext_order_id, charged = provider_api.create_order(agent_service.service.provider,
                                                                  agent_service.service,
                                                                  link, qty)
            except Exception as exc:
                result_list.append({
                    "result": "Exception in provider API, order {}, service: {}, Exception: {}".format(active_order.id,
                                                                                                       agent_service.service.service_id,
                                                                                                       exc)})
                continue

            active_order.spent += charged
            active_order.save()

            service_task = ServiceTask.objects.create(provider=agent_service.service.provider,
                                                      platform=agent_service.service.platform,
                                                      service=agent_service.service,
                                                      link_type=agent_service.service.link_type,
                                                      order=active_order,
                                                      link=link,
                                                      ext_order_id=ext_order_id,
                                                      spent=charged,
                                                      extras="qty={}".format(qty),
                                                      force_complete_after_min=agent_service.service.force_complete_after_min,
                                                      pre_complete_minutes=agent_service.service.pre_complete_minutes)

            result_list.append({
                "result": "Existing the order {}, new service task '{}', link: {}, interval: {}, QTY: {}".format(
                    active_order.name,
                    agent_service.service.service_type.name,
                    link,
                    service_task.pre_complete_minutes,
                    qty)})

    return result_list
