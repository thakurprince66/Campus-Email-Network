from datetime import datetime


devices = {
    "CORE-SW": "ONLINE",
    "CSE-SW": "ONLINE",
    "AI-SW": "ONLINE",
    "ADMIN-SW": "ONLINE",
    "EMAIL-SERVER": "ONLINE"
}


services = {
    "SMTP": "ACTIVE",
    "POP3": "ACTIVE"
}


activity_log = []


def add_log(message):
    time = datetime.now().strftime("%H:%M:%S")
    activity_log.append(f"{time} - {message}")


def get_network_status():
    return devices


def get_services():
    return services


def get_logs():
    return activity_log


# Initial event
add_log("Network monitoring initialized")