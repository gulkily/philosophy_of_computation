import os
import re
from fpdf import FPDF, XPos, YPos
from toc_entry import TOCEntry

class PDFBook(FPDF):
	def __init__(self):
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
			self.set_font("TimesNewRoman", "I", 10)
			self.cell(0, 10, self.current_chapter_title, align="C")
			self.ln(self.header_spacing)
		elif page_no > 1:
			# For front matter pages, show book title
			if not self.is_first_page_of_section():
				self.set_font("TimesNewRoman", "I", 10)
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
		self.set_font("TimesNewRoman", "", 10)
		page_no = self.page_no()
		if self.is_toc_page:
			pass  # No page number on TOC page
		elif self.chapter_start_page is not None and page_no >= self.chapter_start_page:
			page_number = str(page_no - self.chapter_start_page + 1)
			self.cell(0, 10, page_number, align="C")
		elif page_no > 1:
			# Use Roman numerals for front matter
			page_number = self.convert_to_roman(page_no - 1)
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
		# Add background image
		cover_image_path = 'cover_image.jpg'
		if os.path.exists(cover_image_path):
			self.image(cover_image_path, x=0, y=0, w=self.w, h=self.h)
		# Adjust text color for visibility over the image
		self.set_text_color(255, 255, 255)
		# Add title
		self.set_font("TimesNewRoman", "B", 36)
		self.set_xy(0, self.h / 2 - 30)
		self.cell(0, 10, "Philosophy of Computation", align="C")
		# Add subtitle
		self.set_font("TimesNewRoman", "", 18)
		self.ln(15)
		self.cell(0, 10, "An exploration of computational theory, limits, and philosophy", align="C")
		# Add publisher
		self.set_font("TimesNewRoman", "I", 14)
		self.ln(20)
		self.cell(0, 10, "MIT Press", align="C")
		self.set_text_color(0)

	def add_chapter(self, title, content):
		# Update chapter_start_page to the next chapter's start page
		self.chapter_start_page = self.page_no() + 1
		self.current_chapter_title = title
		self.add_page()

		# Add chapter heading at top of first page
		self.set_font("TimesNewRoman", "B", 18)
		self.multi_cell(0, 10, title, align="L")
		self.ln(10)

		# Reset to normal text font for chapter content
		self.set_font("TimesNewRoman", "", 12)
		content = re.sub(r'(?<!\n)\n(?!\n)', ' ', content)
		lines = content.split('\n')
		for line in lines:
			line = line.strip()
			if not line:
				self.ln(4)
			elif line.startswith('##'):
				# Subheading
				subheading = line.strip('# ').strip()
				self.set_font("TimesNewRoman", "B", 14)
				self.ln(6)
				self.cell(0, 10, subheading, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
				self.ln(2)
				self.set_font("TimesNewRoman", "", 12)
			elif re.match(r'!\[.*\]\(.*\)', line):
				# Image
				match = re.match(r'!\[.*\]\((.*)\)', line)
				image_path = match.group(1)
				if os.path.exists(image_path):
					self.image(image_path, w=self.epw)
					self.ln(5)
				else:
					self.multi_cell(0, 6, f'[Image not found: {image_path}]')
			else:
				self.write_markdown_line(line)
		self.ln()
		# Add this chapter to the TOC entries
		self.toc_entries.append(TOCEntry(title=title, page_number=self.chapter_start_page))

	def write_markdown_line(self, text):
		tokens = self.parse_markdown(text)
		for token_text, style in tokens:
			self.set_font("TimesNewRoman", style, 12)
			self.multi_cell(0, 6, token_text, align='J')
			self.set_x(self.l_margin)

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
