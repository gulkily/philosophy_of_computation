# begin photocopy_effect.py

import fitz
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter, ImageChops
import numpy as np
from scipy.ndimage import map_coordinates
from io import BytesIO

def apply_photocopy_effect(input_pdf_path, output_pdf_path, color_mode='mono'):
	def add_photocopy_effect(image, page_number):
		width, height = image.size

		# Convert to appropriate color mode
		if color_mode == 'mono':
			image = image.convert('L')
		else:
			image = image.convert('RGB')

		is_odd_page = (page_number % 2) == 1
		binding_side = 'left' if is_odd_page else 'right'

		# Add toner smudges BEFORE other effects
		image = add_toner_smudges(image, page_number, color_mode)

		image = simulate_page_curl(image, binding_side)
		image = add_dark_edges(image, binding_side)

		angle = np.random.uniform(-0.5, 0.5)
		if color_mode == 'mono':
			bg_color = int(np.median(np.array(image)))
		else:
			bg_color = tuple(map(int, np.median(np.array(image), axis=(0,1))))

		image = image.rotate(angle, expand=True, fillcolor=bg_color)

		left = (image.width - width) // 2
		top = (image.height - height) // 2
		image = image.crop((left, top, left + width, top + height))

		image = add_noise(image)
		image = add_scanlines(image)
		image = adjust_brightness_based_on_text(image)

		if color_mode == 'mono':
			image = image.convert('RGB')
		return image

	def add_toner_smudges(image, page_number, color_mode='mono'):
		width, height = image.size

		# Create a new layer for smudges
		if color_mode == 'mono':
			smudge_layer = Image.new('L', (width, height), 255)
		else:
			smudge_layer = Image.new('RGB', (width, height), (255, 255, 255))

		draw = ImageDraw.Draw(smudge_layer)

		# For testing, make it appear more frequently
		smudge_probability = 0.1  # Temporary high probability for testing
		#print(f"Page {page_number}: Smudge probability {smudge_probability}")

		if np.random.random() < smudge_probability:
			#print(f"Page {page_number}: Creating smudge")
			# Parameters for the band of vertical lines
			band_y = np.random.randint(height // 8, height // 2)
			band_height = np.random.randint(50, 70)

			margin = width * 0.05
			printable_width = width - 2 * margin

			# Increase line density for testing
			line_density = 0.8
			num_lines = int(printable_width * line_density)

			if color_mode == 'mono':
				# Make slightly darker for testing
				base_intensity = np.random.randint(215, 225)

				for i in range(num_lines):
					x = margin + (i * printable_width / num_lines) + np.random.uniform(-1, 1)
					line_height = band_height + np.random.randint(-5, 5)

					# Calculate fade-in over first 20% of height
					fade_height = line_height * 0.7
					for y_offset in range(line_height):
						if y_offset < fade_height:
							# Gradually increase intensity during fade-in
							fade_factor = y_offset / fade_height
							current_intensity = int(255 - ((255 - base_intensity) * fade_factor))
						else:
							# Full intensity for the rest
							current_intensity = base_intensity

						current_intensity += np.random.randint(-3, 3)  # Add slight variation
						current_intensity = min(255, max(220, current_intensity))

						# Draw single pixel
						draw.point((x, band_y + y_offset), fill=current_intensity)

			else:
				colors = {
					'cyan': (230, 255, 255),
					'magenta': (255, 230, 255),
					'yellow': (255, 255, 230),
					'black': (230, 230, 230)
				}

				color_name = np.random.choice(list(colors.keys()))
				base_color = colors[color_name]
				#print(f"Page {page_number}: Using color {color_name}")

				for i in range(num_lines):
					x = margin + (i * printable_width / num_lines) + np.random.uniform(-1, 1)
					line_height = band_height + np.random.randint(-5, 5)

					fade_height = line_height * 0.2
					for y_offset in range(line_height):
						if y_offset < fade_height:
							fade_factor = y_offset / fade_height
							current_color = tuple(int(255 - ((255 - c) * fade_factor)) for c in base_color)
						else:
							current_color = base_color

						# Add slight variation
						color_variation = np.random.randint(-3, 3)
						current_color = tuple(min(255, max(220, c + color_variation)) for c in current_color)

						draw.point((x, band_y + y_offset), fill=current_color)


			# Very light Gaussian blur to softly blend the lines
			smudge_layer = smudge_layer.filter(ImageFilter.GaussianBlur(radius=0.5))

			# Blend smudge layer with original image
			if color_mode == 'mono':
				result = ImageChops.multiply(image, smudge_layer)
				#print(f"Page {page_number}: Applied monochrome blend")
				return result
			else:
				result = Image.blend(image, smudge_layer, 0.3)  # Increased blend factor for testing
				#print(f"Page {page_number}: Applied color blend")
				return result

		#print(f"Page {page_number}: No smudge applied")
		return image  # Return original image if no smudge was applied


	def simulate_page_curl(image, binding_side):
		width, height = image.size
		displacement = np.zeros((height, width, 2), dtype=np.float32)

		# Parameters for the curl effect
		max_vertical_curl = height * 0.015  # Increased vertical displacement
		max_horizontal_curl = width * 0.008  # Added horizontal displacement
		curl_frequency = 1.2  # Controls how rapid the curl is

		# Create coordinate grids
		x_coords = np.linspace(0, 1, width)
		y_coords = np.linspace(0, 1, height)
		X, Y = np.meshgrid(x_coords, y_coords)

		# Calculate distance from binding edge
		if binding_side == 'left':
			distance = X
		else:
			distance = 1 - X

		# Vertical displacement (page curl)
		vertical_curl = max_vertical_curl * np.sin(np.pi * distance * curl_frequency)
		vertical_curl *= (1 - Y * 0.3)  # Reduce effect towards bottom of page

		# Horizontal displacement (page bend)
		horizontal_curl = max_horizontal_curl * (1 - np.cos(np.pi * distance * curl_frequency))
		if binding_side == 'right':
			horizontal_curl = -horizontal_curl

		# Apply graduated effect
		edge_factor = np.exp(-distance * 3)  # Stronger effect near binding
		vertical_curl *= edge_factor
		horizontal_curl *= edge_factor

		# Add subtle wave effect
		wave_amplitude = height * 0.003
		wave_frequency = 4
		wave = wave_amplitude * np.sin(2 * np.pi * Y * wave_frequency)
		vertical_curl += wave * edge_factor

		# Apply displacements
		displacement[:, :, 0] = horizontal_curl  # X displacement
		displacement[:, :, 1] = vertical_curl    # Y displacement

		# Apply the warping
		arr = np.array(image)
		coords = np.indices((height, width), dtype=np.float32)
		coords[0] += displacement[:, :, 1]
		coords[1] += displacement[:, :, 0]

		# Use higher order interpolation for smoother results
		warped_arr = map_coordinates(arr, [coords[0], coords[1]], order=3, mode='reflect')
		warped_arr = np.clip(warped_arr, 0, 255).astype(np.uint8)
		warped_image = Image.fromarray(warped_arr)

		# Round corners after warping
		warped_image = round_corners(warped_image, binding_side)

		return warped_image

	def round_corners(image, binding_side):
		width, height = image.size
		mask = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(mask)
		radius = width * 0.03
		# Add corner rounding on both top and bottom of binding side
		if binding_side == 'left':
			draw.pieslice([0, 0, 2 * radius, 2 * radius], 180, 270, fill=0)
			draw.pieslice([0, height - 2 * radius, 2 * radius, height], 90, 180, fill=0)
		else:
			draw.pieslice([width - 2 * radius, 0, width, 2 * radius], 270, 360, fill=0)
			draw.pieslice([width - 2 * radius, height - 2 * radius, width, height], 0, 90, fill=0)
		image.putalpha(mask)
		image = image.convert('L')
		return image

	def add_dark_edges(image, binding_side):
		width, height = image.size
		edge_width = int(min(width, height) * 0.02)

		# Create base edge mask for all sides
		edge_mask = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(edge_mask)

		# Draw graduated edges on all sides
		for i in range(edge_width):
			shade = int(255 * (1 - (i / edge_width) ** 1.5))  # More pronounced gradient
			draw.rectangle([i, i, width - i - 1, height - i - 1], outline=shade)

		# Blur the edge mask
		edge_mask_blurred = edge_mask.filter(ImageFilter.GaussianBlur(radius=edge_width / 2))
		image = ImageChops.multiply(image, edge_mask_blurred)

		# Enhanced binding shadow effect
		shadow = Image.new('L', (width, height), color=255)
		draw_shadow = ImageDraw.Draw(shadow)

		# Create wider shadow for binding
		binding_width = edge_width * 4  # Wider binding shadow
		shadow_gradient = Image.new('L', (binding_width, height), color=255)
		shadow_draw = ImageDraw.Draw(shadow_gradient)

		# Create graduated binding shadow
		for x in range(binding_width):
			# Calculate base shadow intensity
			progress = x / binding_width
			base_intensity = 255 - (255 * (1 - progress) ** 0.7)  # Adjusted curve

			# Add vertical variation
			for y in range(height):
				y_progress = y / height
				# Darker in the middle, lighter at edges
				y_variation = 1 - 0.15 * np.sin(np.pi * y_progress)
				intensity = int(base_intensity * y_variation)
				intensity = max(0, min(255, intensity))
				shadow_draw.point((x, y), fill=intensity)

		# Add subtle vertical bands for book binding texture
		num_bands = 30
		band_width = height / num_bands
		for i in range(num_bands):
			y_pos = int(i * band_width)
			band_height = int(band_width * 0.8)
			band_intensity = np.random.randint(0, 20)  # Subtle variation
			shadow_draw.rectangle([0, y_pos, binding_width//2, y_pos + band_height],
								fill=255-band_intensity, outline=255-band_intensity)

		# Apply Gaussian blur to smooth the binding texture
		shadow_gradient = shadow_gradient.filter(ImageFilter.GaussianBlur(radius=1))

		# Create second layer of shadow for depth
		deep_shadow_width = int(binding_width * 0.3)
		deep_shadow = Image.new('L', (deep_shadow_width, height), color=255)
		deep_shadow_draw = ImageDraw.Draw(deep_shadow)

		# Draw deeper shadow near binding
		for x in range(deep_shadow_width):
			intensity = int(255 * (x / deep_shadow_width) ** 0.5)
			deep_shadow_draw.line([(x, 0), (x, height)], fill=intensity)

		# Combine shadows based on binding side
		if binding_side == 'left':
			shadow.paste(shadow_gradient, (0, 0))
			shadow.paste(deep_shadow, (0, 0), deep_shadow)
		else:
			shadow_gradient = shadow_gradient.transpose(Image.FLIP_LEFT_RIGHT)
			deep_shadow = deep_shadow.transpose(Image.FLIP_LEFT_RIGHT)
			shadow.paste(shadow_gradient, (width - binding_width, 0))
			shadow.paste(deep_shadow, (width - deep_shadow_width, 0), deep_shadow)

		# Add subtle page thickness shadow
		thickness_shadow = Image.new('L', (width, height), color=255)
		thickness_draw = ImageDraw.Draw(thickness_shadow)
		thickness_width = edge_width * 2

		for x in range(thickness_width):
			intensity = int(245 + (x / thickness_width) * 10)  # Very subtle shadow
			if binding_side == 'left':
				thickness_draw.line([(width - x, 0), (width - x, height)], fill=intensity)
			else:
				thickness_draw.line([(x, 0), (x, height)], fill=intensity)

		# Combine all shadows
		image = ImageChops.multiply(image, shadow)
		image = ImageChops.multiply(image, thickness_shadow)

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
		# Only add scanlines ~20% of the time
		if np.random.random() > 0.2:
			return image
			
		width, height = image.size
		scanlines = Image.new('L', (width, height), 255)
		draw = ImageDraw.Draw(scanlines)

		# Create clusters of scanlines
		num_clusters = int(height * 0.002)  # Fewer clusters
		for _ in range(num_clusters):
			cluster_center = np.random.randint(0, height)
			num_lines = np.random.randint(1, 21)  # 1-21 lines per cluster
			line_spacing = 2  # Closer together

			for i in range(num_lines):
				y = cluster_center + (i * line_spacing)
				if 0 <= y < height:
					intensity = np.random.randint(220, 250)  # Slightly darker lines
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

# end photocopy_effect.py