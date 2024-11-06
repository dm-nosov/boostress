import random

from celery import shared_task
from django.utils import timezone

from boostress.utils import time_difference_min, get_qty
from campaign_manager.models import Order, EngagementConfig, ServiceTask
from delivery_cloud.agent_api import AgentApi
from delivery_cloud.models import Agent, AgentOpResult, OP_SEND, OP_FWD, Endpoint, AgentResource, AgentService
from provider_api.common import APIFactory


@shared_task(bind=True)
def deploy_resource(self, last_message_hrs=4):
    agent = Agent.objects.first()
    endpoints = AgentOpResult.objects.get_available_endpoints(last_message_hrs)

    if not endpoints:
        return {"task": "deploy_resource", "detail": "all endpoints are busy, exiting"}

    endpoint = random.choice(endpoints)
    op_type = random.choice([OP_SEND, OP_FWD])
    last_deployments = AgentOpResult.objects.exclude(endpoint=endpoint).exclude(is_fwd=True)[:10]
    if op_type == OP_FWD and not last_deployments:
        return {"endpoint": endpoint.name, "operation": op_type,  "detail": "Nothing to forward, exiting"}

    if op_type == OP_SEND:
        another_endpoint = Endpoint.objects.exclude(id=endpoint.id).order_by('?')[0]
        out = create_resource(agent, endpoint, another_endpoint)
        return {"endpoint": endpoint.name, "operation": op_type, "ref": another_endpoint.name, "out": out}

    elif op_type == OP_FWD:
        op_resource = random.choice(last_deployments)
        out = fwd_resource(agent, endpoint, op_resource)
        return {"endpoint": endpoint.name, "operation": op_type, "resource": op_resource.ref_url, "out": out}


def create_resource(agent, endpoint, another_endpoint=None):
    resource = AgentResource.objects.filter(is_active=True).order_by('?')[0]
    op_id = 0
    if another_endpoint and random.randint(1, 10) < 3:
        op_id = AgentApi.create(agent.api_url, agent.token, endpoint.ext_id, resource.url, another_endpoint.label)
    else:
        op_id = AgentApi.create(agent.api_url, agent.token, endpoint.ext_id, resource.url, None)

    if op_id == 0:
        return {"status": "error", "details": "CREATE: op_id is 0", "endpoint": endpoint.name, "operation": "create"}

    endpoint.message_qty = op_id
    endpoint.save()
    out = AgentOpResult.objects.create(endpoint=endpoint, ref_id=op_id,
                                       ref_url="{}/{}/{}".format(agent.endpoint_url, endpoint.label,
                                                                 endpoint.message_qty))
    return {"status": "success", "created": out.ref_url}


def fwd_resource(agent, endpoint, op_resource):
    op_id = AgentApi.forward(agent.api_url, agent.token, endpoint.ext_id, op_resource.endpoint.ext_id,
                             op_resource.ref_id)
    if op_id == 0:
        return {"status": "error", "details": "FWD: op_id is 0", "endpoint": endpoint.name, "operation": "create"}

    endpoint.message_qty += 1
    endpoint.save()
    out = AgentOpResult.objects.create(endpoint=endpoint, ref_id=op_id,
                                       ref_url="{}/{}/{}".format(agent.endpoint_url, endpoint.label, endpoint.message_qty),
                                       is_fwd=True)

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
def fulfill_delivery(self, deployment_id):
    deployment = AgentOpResult.objects.get(pk=deployment_id)
    active_order, is_created = Order.objects.get_deployment_order()
    for agent_service in AgentService.objects.all():
        if timezone.now() > active_order.get_last_completed_task_time(deployment.ref_url, agent_service.service):
            engagement_min, engagement_max = EngagementConfig.objects.get_config(link_type=active_order.link_type,
                                                                                 service_type=agent_service.service.service_type,
                                                                                 platform_name=active_order.platform.name)
            time_difference = time_difference_min(deployment.created)

            qty = get_qty(time_difference, active_order.total_followers, agent_service.service.min,
                          agent_service.service.max, engagement_min,
                          engagement_max, False)

            if qty < agent_service.service.min:
                return {
                    "result": "Order {}, qty is {}, attempted the service {}, the QTY is less than {}".format(
                        active_order.name,
                        qty,
                        agent_service.service.service_id,
                        agent_service.service.min)}

            try:
                provider_api = APIFactory.get_api(agent_service.service.provider.api_type)
                ext_order_id, charged = provider_api.create_order(agent_service.service.provider,
                                                                  agent_service.service,
                                                                  deployment.ref_url, qty)
            except Exception as exc:
                return {
                    "result": "Exception in provider API, order {}, service: {}, Exception: {}".format(active_order.id,
                                                                                                       agent_service.service.service_id,
                                                                                                       exc)}

            active_order.spent += charged
            active_order.save()

            service_task = ServiceTask.objects.create(provider=agent_service.service.provider,
                                                      platform=agent_service.service.platform,
                                                      service=agent_service.service,
                                                      link_type=agent_service.service.link_type,
                                                      order=active_order,
                                                      link=deployment.ref_url,
                                                      ext_order_id=ext_order_id,
                                                      spent=charged,
                                                      extras="qty={}".format(qty),
                                                      force_complete_after_min=agent_service.service.force_complete_after_min,
                                                      pre_complete_minutes=agent_service.service.pre_complete_minutes)

            return {
                "result": "Existing the order {}, new service task '{}', interval: {}, QTY: {}".format(
                    active_order.name,
                    agent_service.service.service_type.name,
                    service_task.pre_complete_minutes,
                    qty)}
