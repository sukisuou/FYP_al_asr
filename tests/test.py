import modal

# 1. Define the cloud container environment
# Only needs lightweight web packages for this test
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]",
        "gradio"
    )
)

app = modal.App("counter-test-app")

# 2. Serve the Gradio web UI
@app.function(image=image, max_containers=1, routing_region="ap-south")
@modal.asgi_app()
def ui():
    import gradio as gr
    from fastapi import FastAPI
    from gradio.routes import mount_gradio_app

    def increment(count):
        return count + 1

    with gr.Blocks(title="Modal Test App") as demo:
        gr.Markdown("# 🚀 Modal Deployment Test")
        gr.Markdown("Click the button below to test the cloud state:")
        
        counter = gr.Number(value=0, label="Click Count")
        btn = gr.Button("Click to Increment", variant="primary")
        
        btn.click(fn=increment, inputs=counter, outputs=counter)

    return mount_gradio_app(app=FastAPI(), blocks=demo, path="/")