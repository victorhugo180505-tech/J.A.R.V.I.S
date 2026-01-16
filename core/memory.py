conversation = []

def add_message(role, content):
    conversation.append({
        "role": role,
        "content": content
    })

    # Limitar memoria (últimos 10 mensajes)
    if len(conversation) > 10:
        conversation.pop(0)

def get_conversation():
    return conversation.copy()
