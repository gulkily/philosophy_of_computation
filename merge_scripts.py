import os

def merge_scripts(directory_path, output_file):
	"""
	Merges all Python scripts (.py files) from the specified directory into a single text file.

	Args:
		directory_path (str): Path to the directory containing Python scripts
		output_file (str): Name of the output file
	"""
	# List to store the content of all scripts
	all_content = []

	try:
		# Iterate through all files in the directory
		for filename in os.listdir(directory_path):
			if filename.endswith('.py'):
				file_path = os.path.join(directory_path, filename)

				# Add a header for each file
				all_content.append(f"\n{'='*50}")
				all_content.append(f"File: {filename}")
				all_content.append('='*50 + '\n')

				# Read and append the content of each file
				try:
					with open(file_path, 'r', encoding='utf-8') as file:
						content = file.read()
						all_content.append(content)
				except Exception as e:
					print(f"Error reading {filename}: {str(e)}")

		# Write all content to the output file
		with open(output_file, 'w', encoding='utf-8') as outfile:
			outfile.write('\n'.join(all_content))

		print(f"Successfully merged all Python scripts into {output_file}")

	except Exception as e:
		print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
	# Replace with your directory path containing the Python scripts
	directory_path = "."  # Current directory
	output_file = "merged_scripts.txt"

	merge_scripts(directory_path, output_file)
