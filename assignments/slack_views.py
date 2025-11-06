from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
import hmac, hashlib, time, json
from .ai_engine import run_assignment_pipeline
from .models import Task, Employee

@csrf_exempt
def slack_event(request):
    # verify slack signature (simplified)
    if request.method != "POST":
        return JsonResponse({"ok": True})
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    sig_basestring = f"v0:{timestamp}:{request.body.decode('utf-8')}"
    my_sig = 'v0=' + hmac.new(settings.SLACK_SIGNING_SECRET.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()
    slack_signature = request.headers.get("X-Slack-Signature")
    if not hmac.compare_digest(my_sig, slack_signature):
        return HttpResponseForbidden("invalid signature")
    payload = json.loads(request.body)
    # handle url_verification
    if payload.get("type") == "url_verification":
        return JsonResponse({"challenge": payload.get("challenge")})
    # handle message event
    event = payload.get("event", {})
    text = event.get("text", "")
    user_email = None
    # You can look up user info via Slack API to get an email, but for simplicity we allow task creation without created_by
    task = Task.objects.create(title=text[:200], description=text, status="open")
    res = run_assignment_pipeline(task.id)
    return JsonResponse({"ok": True, "result": res})
