

"""Run a multi-turn customer-support conversation from the command line."""

from agent import handle_support_message
from memory import create_conversation


def main() -> None:
    """Start one customer ticket and continue until the user exits."""

    ticket_customer_id = input("Customer ID: ").strip()

    if not ticket_customer_id:
        print("Customer ID is required.")
        return

    conversation = create_conversation()

    print("Support conversation started.")
    print("Type 'exit' to finish.")

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() in {"exit", "quit"}:
            print("Conversation ended.")
            break

        if not user_message:
            continue

        try:
            answer = handle_support_message(
                ticket_customer_id=ticket_customer_id,
                user_message=user_message,
                conversation=conversation,
            )
        except Exception as error:
            print(f"\nAgent error: {error}")
            continue

        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
