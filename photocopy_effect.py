import fitz
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter, ImageChops
import numpy as np
from scipy.ndimage import map_coordinates
from io import BytesIO

def apply_photocopy_effect(input_pdf_path, output_pdf_path):
	def add_photocopy_effect(image, page_number):
		width, height = image.size
		image = image.convert('L')
		is_odd_page = (page_number % 2) == 1
		binding_side = 'left' if is_odd_page else 'right'
		image = simulate_page_curl(image, binding_side)
		image = add_dark_edges(image, binding_side)
		angle = np.random.uniform(-0.5, 0.5)
		bg_color = int(np.median(np.array(image)))
		image = image.rotate(angle, expand=True, fillcolor=bg_color)
		left = (image.width - width) // 2
		top = (image.height - height) // 2
		image = image.crop((left, top, left + width, top + height))
		image = add_noise(image)
		image = add_scanlines(image)
		image = adjust_brightness_based_on_text(image)
		image = image.convert('RGB')
		return image

	def simulate_page_curl(image, binding_side):
		width, height = image.size
		displacement = np.zeros((height, width, 2), dtype=np.float32)
		max_curl = width * 0.01
		for y in range(height):
			curl = max_curl * np.sin(np.pi * y / height)
			if binding_side == 'left':
				displacement[y, :, 0] += curl
			else:
				displacement[y, :, 0] -= curl
		arr = np.array(image)
		coords = np.indices((height, width), dtype=np.float32)
		coords[0] += displacement[:, :, 1]
		coords[1] += displacement[:, :, 0]
		warped_arr = map_coordinates(arr, [coords[0], coords[1]], order=1, mode='reflect')
		warped_arr = warped_arr.astype(np.uint8)
		warped_image = Image.fromarray(warped_arr)
		warped_image = round_corners(warped_image, binding_side)
		return warped_image

	def round_corners(image, binding_side):
		width, height = image.size
		mask = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(mask)
		radius = width * 0.03
		if binding_side == 'left':
			draw.pieslice([0, 0, 2 * radius, 2 * radius], 180, 270, fill=0)
			draw.rectangle([0, height - radius, radius, height], fill=0)
		else:
			draw.pieslice([width - 2 * radius, 0, width, 2 * radius], 270, 360, fill=0)
			draw.rectangle([width - radius, height - radius, width, height], fill=0)
		image.putalpha(mask)
		image = image.convert('L')
		return image

	def add_dark_edges(image, binding_side):
		width, height = image.size
		edge_width = int(min(width, height) * 0.02)
		edge_mask = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(edge_mask)
		for i in range(edge_width):
			shade = int(255 * (1 - (i / edge_width)))
			draw.rectangle([i, i, width - i - 1, height - i - 1], outline=shade)
		edge_mask_blurred = edge_mask.filter(ImageFilter.GaussianBlur(radius=edge_width / 2))
		image = ImageChops.multiply(image, edge_mask_blurred)
		shadow = Image.new('L', (width, height), color=255)
		draw_shadow = ImageDraw.Draw(shadow)
		max_shadow = 200
		shadow_gradient = Image.new('L', (edge_width * 2, height), color=255)
		for x in range(edge_width * 2):
			alpha = int(255 - (255 * (x / (edge_width * 2))))
			draw_shadow.line([(x, 0), (x, height)], fill=alpha)
		if binding_side == 'left':
			shadow.paste(shadow_gradient, (0, 0))
		else:
			shadow_gradient = shadow_gradient.transpose(Image.FLIP_LEFT_RIGHT)
			shadow.paste(shadow_gradient, (width - edge_width * 2, 0))
		image = ImageChops.multiply(image, shadow)
		return image

	def add_noise(image):
		arr = np.array(image).astype(np.float32)
		noise = np.random.normal(0, 5, arr.shape)
		arr += noise
		arr = np.clip(arr, 0, 255).astype(np.uint8)
		image = Image.fromarray(arr)
		specks = Image.new('L', image.size, color=0)
		draw = ImageDraw.Draw(specks)
		num_specks = int(image.size[0] * image.size[1] * 0.0003)
		for _ in range(num_specks):
			x = np.random.randint(0, image.size[0])
			y = np.random.randint(0, image.size[1])
			draw.point((x, y), fill=255)
		image = ImageChops.screen(image, specks)
		return image

	def add_scanlines(image):
		width, height = image.size
		scanlines = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(scanlines)

		# Add horizontal scanlines
		line_spacing = 3
		for y in range(0, height, line_spacing):
			intensity = np.random.randint(230, 255)  # Slightly darker lines
			draw.line([(0, y), (width, y)], fill=intensity)

		image = ImageChops.multiply(image, scanlines)
		return image

	def adjust_brightness_based_on_text(image):
		arr = np.array(image)
		text_pixels = np.sum(arr < 128)
		total_pixels = arr.size
		text_ratio = text_pixels / total_pixels
		brightness_factor = 1.0 - 0.03 * (text_ratio - 0.5)
		enhancer = ImageEnhance.Brightness(image)
		image = enhancer.enhance(brightness_factor)
		return image

	with fitz.open(input_pdf_path) as doc:
		total_pages = len(doc)
		for page_index in range(total_pages):
			page_number = page_index + 1
			print(f"Applying photocopy effect to page {page_number} of {total_pages}")
			page = doc[page_index]
			pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
			img = Image.open(BytesIO(pix.tobytes()))
			modified_img = add_photocopy_effect(img, page_number)
			img_bytes = BytesIO()
			modified_img.save(img_bytes, format='PNG')
			page.clean_contents()
			rect = page.rect
			page.insert_image(rect, stream=img_bytes.getvalue())
		doc.save(output_pdf_path)
