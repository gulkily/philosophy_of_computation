import argparse
import glob
import os
import re
import sys

from pdf_book import PDFBook
from photocopy_effect import apply_photocopy_effect

def main():
	parser = argparse.ArgumentParser(description="Generate a PDF book with optional testing mode.")
	parser.add_argument('--test', action='store_true', help="Run in test mode (generate only the first 10 pages)")
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

	pdf = PDFBook()

	# Load Times New Roman fonts with a different name
	try:
		pdf.add_font("TimesNewRoman", "", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
		pdf.add_font("TimesNewRoman", "B", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf")
		pdf.add_font("TimesNewRoman", "I", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf")
	except RuntimeError as e:
		sys.exit(f"Error loading fonts: {e}\nPlease ensure Times New Roman fonts are installed in the specified directory.")

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
