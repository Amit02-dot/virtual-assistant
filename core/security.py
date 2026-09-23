import os

class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

def request_permission(action_description, risk_level, speak_func, listen_func):
    """
    Asks the user for confirmation before executing a dangerous action.
    """
    if risk_level == RiskLevel.LOW:
        return True
        
    speak_func(f"Security alert. You are about to {action_description}. This is a {risk_level} risk action. Do you want to proceed? Say yes or no.")
    print(f"[SECURITY] Requesting permission for: {action_description} (Risk: {risk_level})")
    
    response = listen_func()
    if response:
        response_lower = response.lower()
        print(f"[SECURITY] User responded: {response_lower}")
        if any(word in response_lower for word in ["yes", "yeah", "yep", "do it", "proceed", "confirm", "ok", "okay", "sure"]):
            speak_func("Permission granted. Executing.")
            return True
    
    speak_func("Permission denied. Action cancelled.")
    return False

def request_plan_approval(plan_summary, speak_func, listen_func):
    """
    Speaks the generated plan and asks for confirmation to execute.
    """
    speak_func(plan_summary)
    print(f"[SECURITY] Requesting plan approval...")
    
    response = listen_func()
    if response:
        response_lower = response.lower()
        print(f"[SECURITY] User responded to plan: {response_lower}")
        if any(word in response_lower for word in ["yes", "yeah", "yep", "do it", "proceed", "confirm", "ok", "okay", "sure", "execute"]):
            speak_func("Plan approved. Executing now.")
            return True
            
    speak_func("Plan denied. Aborting execution.")
    return False
