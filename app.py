import gradio as gr
import uvicorn
from fastapi import FastAPI
from main import app

# Create Gradio interface that just forwards to FastAPI
def create_gradio_interface():
    # This will wrap our FastAPI app
    interface = gr.mount_gradio_app(app, None, path="/")
    return interface

if __name__ == "__main__":
    # Mount FastAPI app
    demo = create_gradio_interface()

    # Launch the app
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=True
    )