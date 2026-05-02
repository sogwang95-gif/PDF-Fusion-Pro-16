"""
PDF Merger CLI - Windows Console Application
Pure command-line tool for merging PDF files.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple
from PyPDF2 import PdfMerger, PdfReader

class PDFMergerCLI:
    """Main application class for PDF merging operations."""
    
    def __init__(self):
        self.pdf_files: List[Tuple[Path, int]] = []  # (path, size)
        self.output_path = Path.cwd() / "merged_output.pdf"
    
    @staticmethod
    def clear_screen() -> None:
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def get_human_readable_size(size_bytes: int) -> str:
        """Convert file size to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def display_banner(self) -> None:
        """Display application banner."""
        self.clear_screen()
        print("=" * 60)
        print("PDF MERGER CLI".center(60))
        print("Windows Console Application".center(60))
        print("=" * 60)
        print()
    
    def display_file_list(self) -> None:
        """Display current PDF files in list with details."""
        if not self.pdf_files:
            print("📄 No PDF files added yet.")
            print()
            return
        
        print("📋 CURRENT PDF FILES:")
        print("-" * 60)
        print(f"{'#':<4} {'File Name':<40} {'Size':<12}")
        print("-" * 60)
        
        for idx, (file_path, size) in enumerate(self.pdf_files, 1):
            file_name = file_path.name
            if len(file_name) > 37:
                file_name = file_name[:34] + "..."
            size_str = self.get_human_readable_size(size)
            print(f"{idx:<4} {file_name:<40} {size_str:<12}")
        print("-" * 60)
        print(f"Total files: {len(self.pdf_files)}")
        print()
    
    def display_menu(self) -> None:
        """Display main menu options."""
        print("📝 MAIN MENU:")
        print("1. Add PDF files")
        print("2. Move file up")
        print("3. Move file down")
        print("4. Remove selected file")
        print("5. Clear all files")
        print("6. Set output file name")
        print("7. Merge PDFs")
        print("8. Exit")
        print()
    
    def add_pdf_files(self) -> None:
        """Add PDF files to the list."""
        print("📁 Add PDF Files")
        print("-" * 40)
        
        while True:
            file_input = input("Enter PDF file path(s), separated by commas (or 'done'): ").strip()
            
            if file_input.lower() == 'done':
                break
            
            if not file_input:
                continue
            
            files = [f.strip() for f in file_input.split(',')]
            added_count = 0
            
            for file_str in files:
                try:
                    file_path = Path(file_str)
                    
                    # Check if file already exists in list
                    if any(str(fp[0]) == str(file_path) for fp in self.pdf_files):
                        print(f"⚠️  '{file_path.name}' is already in the list.")
                        continue
                    
                    # Validate file
                    if not file_path.exists():
                        print(f"❌ File not found: {file_path}")
                        continue
                    
                    if file_path.suffix.lower() != '.pdf':
                        print(f"❌ Not a PDF file: {file_path}")
                        continue
                    
                    # Check if file is readable PDF
                    try:
                        with open(file_path, 'rb') as f:
                            PdfReader(f)
                        file_size = file_path.stat().st_size
                        self.pdf_files.append((file_path, file_size))
                        added_count += 1
                        print(f"✅ Added: {file_path.name}")
                    except Exception as e:
                        print(f"❌ Invalid PDF file: {file_path.name} ({str(e)})")
                        
                except Exception as e:
                    print(f"❌ Error processing file: {file_str} ({str(e)})")
            
            if added_count > 0:
                print(f"✓ Added {added_count} file(s) to the list.")
            
            if len(files) == 1 and files[0]:
                # Single file entry, ask if they want to add more
                more = input("Add more files? (y/n): ").lower()
                if more != 'y':
                    break
    
    def move_file_up(self) -> None:
        """Move selected file up in the list."""
        if not self.pdf_files:
            print("❌ No files to move.")
            return
        
        try:
            file_num = int(input(f"Enter file number to move up (1-{len(self.pdf_files)}): "))
            if 1 <= file_num <= len(self.pdf_files):
                if file_num == 1:
                    print("⚠️  File is already at the top.")
                else:
                    index = file_num - 1
                    self.pdf_files[index], self.pdf_files[index-1] = self.pdf_files[index-1], self.pdf_files[index]
                    print(f"✓ Moved file #{file_num} up one position.")
            else:
                print(f"❌ Invalid file number. Please enter 1-{len(self.pdf_files)}.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def move_file_down(self) -> None:
        """Move selected file down in the list."""
        if not self.pdf_files:
            print("❌ No files to move.")
            return
        
        try:
            file_num = int(input(f"Enter file number to move down (1-{len(self.pdf_files)}): "))
            if 1 <= file_num <= len(self.pdf_files):
                if file_num == len(self.pdf_files):
                    print("⚠️  File is already at the bottom.")
                else:
                    index = file_num - 1
                    self.pdf_files[index], self.pdf_files[index+1] = self.pdf_files[index+1], self.pdf_files[index]
                    print(f"✓ Moved file #{file_num} down one position.")
            else:
                print(f"❌ Invalid file number. Please enter 1-{len(self.pdf_files)}.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def remove_selected_file(self) -> None:
        """Remove selected file from the list."""
        if not self.pdf_files:
            print("❌ No files to remove.")
            return
        
        self.display_file_list()
        
        try:
            file_num = int(input(f"Enter file number to remove (1-{len(self.pdf_files)}): "))
            if 1 <= file_num <= len(self.pdf_files):
                file_name = self.pdf_files[file_num-1][0].name
                confirm = input(f"⚠️  Remove '{file_name}'? (y/n): ").lower()
                if confirm == 'y':
                    removed_file = self.pdf_files.pop(file_num-1)
                    print(f"✓ Removed: {removed_file[0].name}")
                else:
                    print("✗ Removal cancelled.")
            else:
                print(f"❌ Invalid file number. Please enter 1-{len(self.pdf_files)}.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def clear_all_files(self) -> None:
        """Clear all files from the list."""
        if not self.pdf_files:
            print("❌ No files to clear.")
            return
        
        confirm = input("⚠️  Clear ALL files from the list? (y/n): ").lower()
        if confirm == 'y':
            file_count = len(self.pdf_files)
            self.pdf_files.clear()
            print(f"✓ Cleared all {file_count} file(s).")
        else:
            print("✗ Clear operation cancelled.")
    
    def set_output_filename(self) -> None:
        """Set the output PDF file name."""
        print("💾 Set Output File Name")
        print(f"Current: {self.output_path}")
        print()
        
        new_name = input("Enter new output file name (or press Enter to keep current): ").strip()
        
        if new_name:
            if not new_name.lower().endswith('.pdf'):
                new_name += '.pdf'
            
            try:
                # Create Path object to validate
                new_path = Path(new_name)
                if new_path.is_absolute():
                    self.output_path = new_path
                else:
                    self.output_path = Path.cwd() / new_path
                
                print(f"✓ Output file set to: {self.output_path}")
            except Exception as e:
                print(f"❌ Invalid file path: {str(e)}")
        else:
            print("✗ Output file name unchanged.")
    
    def merge_pdfs(self) -> None:
        """Merge all PDF files in the list."""
        if len(self.pdf_files) < 2:
            print("❌ Need at least 2 PDF files to merge.")
            return
        
        print("🔄 Merging PDFs...")
        print(f"Output file: {self.output_path}")
        print(f"Total files to merge: {len(self.pdf_files)}")
        print()
        
        # Check if output file already exists
        if self.output_path.exists():
            overwrite = input(f"⚠️  '{self.output_path.name}' already exists. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("✗ Merge cancelled.")
                return
        
        merger = PdfMerger()
        success_count = 0
        
        try:
            for idx, (file_path, _) in enumerate(self.pdf_files, 1):
                print(f"Processing {idx}/{len(self.pdf_files)}: {file_path.name}")
                
                try:
                    with open(file_path, 'rb') as f:
                        merger.append(f)
                    success_count += 1
                except Exception as e:
                    print(f"  ⚠️  Warning: Could not read '{file_path.name}' ({str(e)})")
                    continue
            
            if success_count == 0:
                print("❌ No valid PDF files could be processed.")
                return
            
            print(f"\n✓ Successfully processed {success_count} of {len(self.pdf_files)} files.")
            print("Writing output file...")
            
            # Write merged PDF
            with open(self.output_path, 'wb') as output_file:
                merger.write(output_file)
            
            output_size = self.output_path.stat().st_size
            size_str = self.get_human_readable_size(output_size)
            
            print("=" * 60)
            print("✅ MERGE COMPLETE!")
            print(f"Output: {self.output_path}")
            print(f"Size: {size_str}")
            print(f"Pages merged: {success_count} files")
            print("=" * 60)
            
        except PermissionError:
            print(f"❌ Permission denied: Cannot write to '{self.output_path}'")
            print("  Try closing the file if it's open in another program.")
        except Exception as e:
            print(f"❌ Merge failed: {str(e)}")
        finally:
            merger.close()
    
    def run(self) -> None:
        """Main application loop."""
        self.display_banner()
        
        while True:
            self.display_file_list()
            self.display_menu()
            
            try:
                choice = input("Enter choice (1-8): ").strip()
                
                if choice == '1':
                    self.add_pdf_files()
                elif choice == '2':
                    self.move_file_up()
                elif choice == '3':
                    self.move_file_down()
                elif choice == '4':
                    self.remove_selected_file()
                elif choice == '5':
                    self.clear_all_files()
                elif choice == '6':
                    self.set_output_filename()
                elif choice == '7':
                    self.merge_pdfs()
                elif choice == '8':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-8.")
                
                # Pause to let user read messages
                if choice in ['1', '4', '5', '7']:
                    input("\nPress Enter to continue...")
                
                self.display_banner()
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation interrupted by user.")
                continue_choice = input("Exit program? (y/n): ").lower()
                if continue_choice == 'y':
                    print("\n👋 Goodbye!")
                    break
                else:
                    self.display_banner()
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                input("\nPress Enter to continue...")
                self.display_banner()


def main() -> None:
    """Application entry point."""
    try:
        # Check for PyPDF2 availability
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 is not installed.")
        print("Please install it using: pip install PyPDF2")
        sys.exit(1)
    
    app = PDFMergerCLI()
    app.run()


if __name__ == "__main__":
    main()