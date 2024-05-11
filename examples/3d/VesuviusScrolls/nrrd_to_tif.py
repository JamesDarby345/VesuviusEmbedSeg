import os
import nrrd
import tifffile

def nrrd_to_tif(directory):
    """
    Converts all .nrrd files in a directory and its subdirectories to .tif format.
    
    Parameters:
        directory (str): The path to the directory to search for .nrrd files.
    """
    # Walk through all directories and files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file is a .nrrd file
            if file.endswith('.nrrd'):
                # Full path to the current .nrrd file
                nrrd_path = os.path.join(root, file)
                # Load the .nrrd file
                data, header = nrrd.read(nrrd_path)
                # Define the corresponding .tif file path
                tif_path = nrrd_path.replace('.nrrd', '.tif')
                # Save the data as a .tif file
                tifffile.imwrite(tif_path, data)
                print(f"Converted {nrrd_path} to {tif_path}")

# Usage example, replace 'path_to_folder' with the actual path
directory_path = '/home/james/Documents/VS/EmbedSegScrolls/EmbedSeg/data/labelled_cubes'
nrrd_to_tif(directory_path)
