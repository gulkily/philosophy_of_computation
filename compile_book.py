# begin compile_book.py

import argparse
import glob
import os
import re
import sys

from pdf_book import PDFBook
from photocopy_effect import apply_photocopy_effect

def find_font_path(font_name, style=""):
	"""Find the correct font path by checking common locations"""
	garamond_paths = {
		"": "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Regular.ttf",
		"B": "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Bold.ttf",
		"I": "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Italic.ttf"
	}

	if font_name == "EBGaramond":
		return garamond_paths.get(style)
	return None

def main():
	parser = argparse.ArgumentParser(description="Generate a PDF book with optional testing mode.")
	parser.add_argument('--test', action='store_true', help="Run in test mode (generate only the first 10 pages)")
	parser.add_argument('--no-effect', action='store_true', help="Skip applying the photocopy effect")
	parser.add_argument('--blank-cover', action='store_true', help="Use a blank cover page without image")
	parser.add_argument('--font', choices=['garamond', 'times', 'dejavu', 'noto'],
					   default='garamond', help="Choose the font family (default: garamond)")
	args = parser.parse_args()

	# Collect chapters
	chapter_files = sorted([file for file in glob.glob("*.txt") if re.match(r'\d+_', file)])

	chapters = []
	for i, filename in enumerate(chapter_files, start=1):
		try:
			with open(filename, "r", encoding="utf-8") as file:
				title_line = file.readline().strip()
				title = title_line.strip("# ").replace(f"Chapter {i}:", "").strip()
				content = file.read()
				chapters.append((title, content))
		except FileNotFoundError:
			print(f"Warning: Chapter file {filename} not found")
		except Exception as e:
			print(f"Error processing chapter {filename}: {e}")

	pdf = PDFBook(blank_cover=args.blank_cover)
	pdf.font_preferences = []
	fonts_loaded = False

	if args.font == 'garamond':
		regular_font = "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Regular.ttf"
		bold_font = "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Bold.ttf"
		italic_font = "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Italic.ttf"

		if all(os.path.exists(f) for f in [regular_font, bold_font, italic_font]):
			try:
				pdf.add_font("EBGaramond", "", regular_font)
				pdf.add_font("EBGaramond", "B", bold_font)
				pdf.add_font("EBGaramond", "I", italic_font)
				fonts_loaded = True
				print("EB Garamond fonts loaded successfully")
				pdf.font_preferences.append("EBGaramond")
			except RuntimeError as e:
				print(f"Could not load EB Garamond fonts: {e}")
		else:
			print("Could not find EB Garamond font files. Make sure fonts-ebgaramond is installed.")
			
	if args.font == 'times' or (args.font == 'garamond' and not fonts_loaded):
		try:
			pdf.add_font("TimesNewRoman", "", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
			pdf.add_font("TimesNewRoman", "B", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf")
			pdf.add_font("TimesNewRoman", "I", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf")
			fonts_loaded = True
			print("Times New Roman fonts loaded successfully")
			pdf.font_preferences.append("TimesNewRoman")
		except RuntimeError as e:
			print(f"Could not load Times New Roman fonts: {e}")

	if args.font == 'dejavu' or not fonts_loaded:
		try:
			pdf.add_font("DejaVuSerif", "", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
			pdf.add_font("DejaVuSerif", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf") 
			pdf.add_font("DejaVuSerif", "I", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf")
			fonts_loaded = True
			print("DejaVu Serif fonts loaded successfully")
			pdf.font_preferences.append("DejaVuSerif")
		except RuntimeError as e:
			print(f"Could not load DejaVu Serif fonts: {e}")

	if args.font == 'noto' or not fonts_loaded:
		try:
			pdf.add_font("NotoSerif", "", "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf")
			pdf.add_font("NotoSerif", "B", "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf")
			pdf.add_font("NotoSerif", "I", "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf")
			fonts_loaded = True
			print("Noto Serif fonts loaded successfully")
			pdf.font_preferences.append("NotoSerif")
		except RuntimeError as e:
			print(f"Could not load Noto Serif fonts: {e}")

	if not pdf.font_preferences:
		sys.exit("Error: No fonts could be loaded. Please install at least one of: EB Garamond, Times New Roman, DejaVu Serif, or Noto Serif")

	# Add cover page
	pdf.add_cover_page()

	# Add chapters and collect TOC entries
	max_pages = 10 if args.test else None
	for i, (title, content) in enumerate(chapters, start=1):
		if max_pages and pdf.page_no() >= max_pages:
			print("Test mode active: Only the first 10 pages are generated.")
			break
		pdf.add_chapter(title, content)

	output_pdf = "Philosophy_of_Computation_Book.pdf" if not args.test else "Philosophy_of_Computation_Book_TEST.pdf"

	try:
		if args.no_effect:
			pdf.output(output_pdf)
			print(f"PDF successfully created without photocopy effect: {output_pdf}")
		else:
			pdf.output("temp_book.pdf")
			# Apply photocopy effect to the final PDF
			apply_photocopy_effect("temp_book.pdf", output_pdf)
			os.remove("temp_book.pdf")
			print(f"PDF successfully created with photocopy effect: {output_pdf}")
	except Exception as e:
		print(f"Error saving PDF: {e}")
		if os.path.exists("temp_book.pdf"):
			os.remove("temp_book.pdf")

if __name__ == "__main__":
	main()

# end compile_book.py