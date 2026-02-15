import os
import requests
import datetime
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY or "sk-or-" not in API_KEY:
    print("Missing or invalid API key.")
    exit()

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
console = Console()


def log_chat(chat_history, filename="chat_log.md"):
    """Save a beautifully formatted chat log in Markdown with timestamps."""
    if not chat_history:
        return
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"# Chat Session at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for msg in chat_history:
                timestamp = msg.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                role = msg["role"].capitalize()
                f.write(f"**{role}** [{timestamp}]:\n")
                for line in msg["content"].splitlines():
                    f.write(f"{line}\n")
                f.write("\n---\n\n")
        console.print(f"(Chat saved to {filename})", style="dim")
    except Exception as e:
        console.print(f"Failed to save chat: {e}", style="bold red")


def load_prompt(file_number):
    path = f"prompts/{file_number}.txt"
    if not os.path.isfile(path):
        console.print(f"Prompt file not found: {path}", style="bold red")
        exit()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def select_mode():
    console.print("\nWelcome to AI. Choose a mode:\n", style="bold magenta")
    console.print("1. Lyra – prompt optimizer")
    console.print("2. Echo – message rewriter")
    console.print("3. Ghostwriter – story assistant")
    console.print("4. Codex – code helper")
    console.print("5. Plain – no system prompt\n")
    choice = Prompt.ask("Pick 1, 2, 3, 4 or 5").strip()
    if choice not in {"1", "2", "3", "4", "5"}:
        console.print("Invalid choice. Exiting.", style="bold red")
        exit()
    return choice


def select_model(current_model=None):
    """Let user paste a model or keep current."""
    if current_model:
        console.print(f"\nCurrently using model: [bold cyan]{current_model}[/]")
        change = Prompt.ask("Change model? Paste new model or press Enter to keep current").strip()
        if change:
            return change
        return current_model
    else:
        model = Prompt.ask("Paste model name to use (e.g., openai/gpt-oss-120b:free)").strip()
        return model or "openai/gpt-oss-120b:free"


def chat_loop(chat_history, model):
    console.print("\nType 'exit' to quit.\n", style="dim")
    while True:
        user_input = Prompt.ask("[bold blue]You[/]").strip()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if user_input.lower() in {"exit", "quit", "bye"}:
            console.print("[bold green]AI: Later.[/]")
            break

        if not user_input:
            console.print("[bold green]AI: Say something.[/]")
            continue

        chat_history.append({"role": "user", "content": user_input, "timestamp": timestamp})
        payload = {"model": model, "messages": chat_history}

        for attempt in range(3):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=HEADERS,
                    json=payload,
                    timeout=10
                )
                if response.status_code != 200:
                    console.print(f"HTTP {response.status_code}: {response.text}", style="red")
                    time.sleep(1)
                    continue

                data = response.json()
                AI_reply = data["choices"][0]["message"]["content"].strip()
                chat_history.append({
                    "role": "assistant",
                    "content": AI_reply,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Display nicely in rich
                panel = Panel.fit(Markdown(AI_reply), title=f"AI [{datetime.datetime.now().strftime('%H:%M:%S')}]", border_style="green")
                console.print(panel)
                break

            except Exception as e:
                console.print(f"Error talking to AI (attempt {attempt + 1}): {e}", style="red")
                time.sleep(1)
        else:
            console.print("[bold red]Failed to get a response after 3 attempts. Moving on.[/]")

        # Mid-chat model change
        if user_input.lower().startswith("/model"):
            model = select_model(current_model=model)
            console.print(f"[bold cyan]Switched to model: {model}[/]")


if __name__ == "__main__":
    mode = select_mode()
    chat_history = []

    if mode != "5":
        system_prompt = load_prompt(mode)
        chat_history.append({
            "role": "system",
            "content": system_prompt,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    model = select_model()
    chat_loop(chat_history, model)
    log_chat(chat_history)
