from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import jobs,notifications

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Scheduler",
    description="Async job queue system",
    version="1.0.0"
)

# Include routers
app.include_router(jobs.router)
app.include_router(notifications.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "Job Scheduler API", "docs": "/docs"}
# from fastapi import FastAPI, WebSocket
# from fastapi.responses import HTMLResponse



# Optional: simple HTML page to test visually
# html = """
# <!DOCTYPE html>
# <html>
#   <head>
#     <title>WebSocket Test</title>
#   </head>
#   <body>
#     <h1>WebSocket Test</h1>
#     <ul id="messages"></ul>
#     <input id="msgInput" type="text" placeholder="Type message..."/>
#     <button onclick="sendMessage()">Send</button>
#     <script>
#       const ws = new WebSocket("ws://localhost:8000/ws-test");
#       ws.onopen = () => console.log("Connected!");
#       ws.onmessage = (event) => {
#         const li = document.createElement("li");
#         li.textContent = event.data;
#         document.getElementById("messages").appendChild(li);
#       };
#       function sendMessage() {
#         const input = document.getElementById("msgInput");
#         ws.send(input.value);
#         input.value = "";
#       }
#     </script>
#   </body>
# </html>
# """

# @app.get("/ws-test-page")
# async def ws_test_page():
#     return HTMLResponse(html)


# @app.websocket("/ws-test")
# async def websocket_test(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_text("✅ Connection established!")

#     try:
#         while True:
#             msg = await websocket.receive_text()
#             await websocket.send_text(f"You sent: {msg}")
#     except Exception as e:
#         print(f"WebSocket closed: {e}")
