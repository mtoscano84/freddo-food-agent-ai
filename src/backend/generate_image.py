import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# TODO(developer): Update and un-comment below lines
# PROJECT_ID = "your-project-id"
output_file = "output-image.png"  # Uncomment and specify your desired output filename
# prompt = "" # The text prompt describing what you want to see.

vertexai.init(project="freddo-project", location="us-central1")

model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

images = model.generate_images(
    prompt="Gazapacho",
    # Optional parameters
    number_of_images=1,
    language="en",
    # You can't use a seed value and watermark at the same time.
    # add_watermark=False,
    # seed=100,
    aspect_ratio="1:1",
    safety_filter_level="block_some",
    person_generation="allow_adult",
)

images[0].save(location=output_file, include_generation_parameters=False)

# Optional. View the generated image in a notebook.
# images[0].show()

print(f"Created output image using {len(images[0]._image_bytes)} bytes")
# Example response:
# Created output image using 1234567 bytes