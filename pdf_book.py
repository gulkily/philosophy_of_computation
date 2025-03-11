# begin pdf_book.py

"""
PDFBook - A PDF book generation class built on FPDF

This module provides functionality for generating PDF books with professional formatting,
including chapters, table of contents, headers/footers, and Markdown-style text formatting.

Key features:
- Cover page generation with SVG/JPG support
- Chapter organization with proper page numbering
- Headers showing chapter titles
- Footers with page numbers (Roman numerals for front matter)
- Font fallback system for reliable text rendering
- Markdown parsing for italic text
- Image embedding support
- Configurable margins and spacing

Code structure:
- PDFBook class inherits from FPDF
- Font handling methods:
  - set_font_with_fallback(): Manages font selection and fallback
- Page structure methods:  
  - header(): Renders page headers based on context
  - footer(): Handles page numbering
  - add_cover_page(): Creates cover with image and text
- Content methods:
  - add_chapter(): Processes chapter content with Markdown
  - write_markdown_line(): Handles line-level Markdown
  - parse_markdown(): Tokenizes Markdown syntax
- Helper methods:
  - convert_to_roman(): Generates Roman numerals
  - is_first_page_of_section(): Detects section starts
"""

import os
import re
from fpdf import FPDF, XPos, YPos
from toc_entry import TOCEntry

class PDFBook(FPDF):
	def __init__(self, blank_cover=False):
		super().__init__()
		self.set_margins(30, 25, 30)  # Wider margins for a professional look
		self.set_auto_page_break(auto=True, margin=25)
		self.alias_nb_pages()
		self.toc_entries = []
		self.header_spacing = 10
		self.current_chapter_title = ''
		self.chapter_start_page = None
		self.toc_page_number = None
		self.is_toc_page = False
		self.font_preferences = []  # Start empty, will be populated with successfully loaded fonts
		self.active_font = None
		self.blank_cover = blank_cover

	def set_font_with_fallback(self, style, size, text=""):
		if not self.active_font:
			# Try each font until we find one that works
			for font in self.font_preferences:
				try:
					self.set_font(font, style, size)
					if not text or self.get_string_width(text) > 0:
						self.active_font = font
						break
				except RuntimeError:
					continue
			if not self.active_font:
				raise RuntimeError("No usable fonts found")
		else:
			# Check if current font can handle the text
			try:
				self.set_font(self.active_font, style, size)
				if text and self.get_string_width(text) == 0:
					# Current font missing glyphs, try others
					for font in self.font_preferences:
						if font != self.active_font:
							try:
								self.set_font(font, style, size)
								if self.get_string_width(text) > 0:
									self.active_font = font
									break
							except RuntimeError:
								continue
			except RuntimeError:
				# Current font failed, try others
				self.active_font = None
				self.set_font_with_fallback(style, size, text)

	def header(self):
		page_no = self.page_no()
		if self.is_toc_page:
			# No header text for table of contents, just spacing
			self.ln(self.header_spacing)
		elif self.chapter_start_page is not None and page_no == self.chapter_start_page:
			# Suppress header on the first page of a chapter
			self.ln(self.header_spacing)
		elif self.chapter_start_page is not None and page_no > self.chapter_start_page:
			# For subsequent pages of the chapter, show the chapter title
			self.set_font_with_fallback("I", 10, self.current_chapter_title)
			self.cell(0, 10, self.current_chapter_title, align="C")
			self.ln(self.header_spacing)
		elif page_no > 1:
			# For front matter pages, show book title
			if not self.is_first_page_of_section():
				self.set_font_with_fallback("I", 10, "Philosophy of Computation")
				self.cell(0, 10, "Philosophy of Computation", align="C")
			self.ln(self.header_spacing)
		else:
			# No header on the cover page, just spacing
			self.ln(self.header_spacing)

	def is_first_page_of_section(self):
		# Helper method to detect first pages of sections
		page_no = self.page_no()
		# Check if this is the first page of a new section
		# This can be expanded based on how sections are determined
		return page_no == 1 or page_no == self.toc_page_number

	def footer(self):
		self.set_y(-25)
		page_no = self.page_no()
		if page_no == 1:
			pass  # No page number on cover page
		elif self.is_toc_page:
			pass  # No page number on TOC page
		elif page_no > 1:
			# Use Roman numerals for front matter, regular numbers for chapters
			if self.chapter_start_page is None:
				page_number = self.convert_to_roman(page_no - 1)
			else:
				page_number = str(page_no)
			self.set_font_with_fallback("", 10, page_number)
			self.cell(0, 10, page_number, align="C")

	def convert_to_roman(self, num):
		val = [
			1000, 900, 500, 400,
			100, 90, 50, 40,
			10, 9, 5, 4,
			1
		]
		syms = [
			"M", "CM", "D", "CD",
			"C", "XC", "L", "XL",
			"X", "IX", "V", "IV",
			"I"
		]
		roman_num = ''
		i = 0
		while num > 0:
			for _ in range(num // val[i]):
				roman_num += syms[i]
				num -= val[i]
			i += 1
		return roman_num

	def add_cover_page(self):
		self.add_page()

		if self.blank_cover:
			return	

		# Try SVG first, then fall back to JPG if SVG fails
		try:
			import cairosvg
			from PIL import Image
			import io

			# Convert SVG to PNG in memory
			svg_path = 'cover.svg'
			if os.path.exists(svg_path):
				png_data = cairosvg.svg2png(url=svg_path)

				# Create PIL Image from PNG data
				cover_image = Image.open(io.BytesIO(png_data))

				# Get dimensions
				img_width, img_height = cover_image.size

				# Calculate scaling to fit page
				width_ratio = self.w / img_width
				height_ratio = self.h / img_height
				scale = min(width_ratio, height_ratio)

				# Calculate centered position
				x = (self.w - (img_width * scale)) / 2
				y = (self.h - (img_height * scale)) / 2

				# Save temporary PNG file
				temp_png = "temp_cover.png"
				with open(temp_png, "wb") as f:
					f.write(png_data)

				# Add image to PDF
				self.image(temp_png, x, y, w=img_width * scale)

				# Clean up temporary file
				os.remove(temp_png)
				return

		except (ImportError, Exception) as e:
			print(f"SVG processing failed, falling back to JPG: {e}")

		# Fall back to existing JPG cover logic
		cover_image_path = 'cover_image.jpg'
		if os.path.exists(cover_image_path):
			self.image(cover_image_path, x=0, y=0, w=self.w, h=self.h)

		# Add text elements (preserved from original)
		self.set_text_color(255, 255, 255)

		# Add title
		title = "Philosophy of Computation"
		self.set_font_with_fallback("B", 36, title)
		self.set_xy(0, self.h / 2 - 30)
		self.cell(0, 10, title, align="C")

		# Add subtitle
		subtitle = "An exploration of computational theory, limits, and philosophy"
		self.set_font_with_fallback("", 18, subtitle)
		self.ln(15)
		self.cell(0, 10, subtitle, align="C")

		# Add publisher
		publisher = "MIT Press"
		self.set_font_with_fallback("I", 14, publisher)
		self.ln(20)
		self.cell(0, 10, publisher, align="C")
		self.set_text_color(0)

	def add_chapter(self, title, content):
		# Update chapter_start_page to the next chapter's start page
		self.chapter_start_page = self.page_no() + 1
		self.current_chapter_title = title
		self.add_page()

		# Add chapter heading at top of first page
		self.set_font_with_fallback("B", 18, title)
		self.multi_cell(0, 10, title, align="L")
		self.ln(10)

		# Reset to normal text font for chapter content
		self.set_font_with_fallback("", 12)
		content = re.sub(r'(?<!\n)\n(?!\n)', ' ', content)
		lines = content.split('\n')
		for line in lines:
			line = line.strip()
			if not line:
				self.ln(4)
			elif line.startswith('##'):
				# Subheading
				subheading = line.strip('# ').strip()
				self.set_font_with_fallback("B", 14, subheading)
				self.ln(6)
				self.cell(0, 10, subheading, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
				self.ln(2)
				self.set_font_with_fallback("", 12)
			elif re.match(r'!\[.*\]\(.*\)', line):
				# Image
				match = re.match(r'!\[.*\]\((.*)\)', line)
				image_path = match.group(1)
				if os.path.exists(image_path):
					self.image(image_path, w=self.epw)
					self.ln(5)
				else:
					error_msg = f'[Image not found: {image_path}]'
					self.set_font_with_fallback("", 12, error_msg)
					self.multi_cell(0, 6, error_msg)
			else:
				self.write_markdown_line(line)
		self.ln()
		# Add this chapter to the TOC entries
		self.toc_entries.append(TOCEntry(title=title, page_number=self.chapter_start_page))

	def write_markdown_line(self, text):
		tokens = self.parse_markdown(text)
		for token_text, style in tokens:
			self.set_font_with_fallback(style, 12, token_text)
			self.write(6, token_text)
		self.ln()  # Add line break at the end of the complete line

	def parse_markdown(self, text):
		tokens = []
		pattern = re.compile(r'(\*[^*]+\*)')
		last_end = 0
		for match in pattern.finditer(text):
			if match.start() > last_end:
				tokens.append((text[last_end:match.start()], ''))
			tokens.append((match.group(1).strip('*'), 'I'))
			last_end = match.end()
		if last_end < len(text):
			tokens.append((text[last_end:], ''))
		return tokens

# end pdf_book.py