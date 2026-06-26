from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import random
import string
from datetime import datetime
import os

# === CONFIG ===
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyCYpSpBr9Q6ks83d_HKeKdzaQRY-DVSU0s"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI(title="AI Enterprise Assistant", version="1.0")

# === CONVERSATION MEMORY ===
conversation_history = []

# === MOCK DATABASE ===
tickets = []
employees = [
    {"id": 1, "name": "Rahul Sharma", "department": "Engineering", "status": "Active"},
    {"id": 2, "name": "Priya Singh", "department": "HR", "status": "Active"},
    {"id": 3, "name": "Amit Patel", "department": "Sales", "status": "On Leave"},
]

# === REQUEST MODEL ===
class Question(BaseModel):
    question: str

# === TICKET CREATOR ===
def create_ticket(question: str):
    ticket_id = "TKT" + "".join(random.choices(string.digits, k=5))
    ticket = {
        "ticket_id": ticket_id,
        "issue": question,
        "status": "Open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tickets.append(ticket)
    return ticket

# === REPORT GENERATOR ===
def generate_report():
    active = [e for e in employees if e["status"] == "Active"]
    on_leave = [e for e in employees if e["status"] == "On Leave"]
    open_tickets = [t for t in tickets if t["status"] == "Open"]
    return {
        "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_employees": len(employees),
        "active_employees": len(active),
        "employees_on_leave": len(on_leave),
        "total_tickets_raised": len(tickets),
        "open_tickets": len(open_tickets),
        "ticket_details": open_tickets
    }

# === MAIN ENDPOINT ===
@app.post("/ask")
async def ask(payload: Question):
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if len(question) < 3:
        raise HTTPException(status_code=400, detail="Question too short, please be more specific")

    q = question.lower()

    # Business action — ticket creation
    if any(word in q for word in ["create ticket", "raise ticket", "open ticket", "new ticket"]):
        ticket = create_ticket(question)
        return {
            "type": "business_action",
            "action": "ticket_created",
            "data": ticket,
            "message": f"Ticket {ticket['ticket_id']} created successfully."
        }

    # Business action — generate report
    if any(word in q for word in ["generate report", "show report", "get report", "report"]):
        report = generate_report()
        return {
            "type": "business_action",
            "action": "report_generated",
            "data": report,
            "message": "Report generated successfully."
        }

    # Business action — fetch employee info
    if any(word in q for word in ["employee", "staff", "team", "who is", "workers"]):
        return {
            "type": "business_action",
            "action": "employee_fetch",
            "data": employees,
            "message": "Here is the current employee information."
        }

    # LLM with conversation memory
    conversation_history.append(f"User: {question}")
    recent = conversation_history[-10:]
    context = "\n".join(recent)

    prompt = f"""You are an enterprise AI assistant helping employees with business queries.
Be professional, concise and helpful. If the question is unclear or ambiguous, ask for clarification politely.

Conversation so far:
{context}

Now answer the latest question."""

    try:
        response = model.generate_content(prompt)
        answer = response.text
        conversation_history.append(f"Assistant: {answer}")
    except Exception as e:
        answer = "I'm having trouble processing that right now. Please try rephrasing your question or try again in a moment."

    return {
        "type": "llm_response",
        "question": question,
        "answer": answer
    }

# === HEALTH CHECK ===
@app.get("/")
def root():
    return {
        "status": "AI Enterprise Assistant is running",
        "version": "1.0",
        "endpoints": ["/ask", "/docs"]
    }