"""
PowerPoint COM automation for notes synchronization.
"""
import os
from typing import Dict

class NotesSync:
    """Handles slide notes synchronization using PowerPoint COM"""
    
    def sync_notes(self, pptx_path: str, slide_scripts: Dict[int, str]):
        """
        Use PowerPoint COM to synchronize slide notes.
        
        Args:
            pptx_path: Absolute path to PPTX file
            slide_scripts: Dict mapping slide number to script text
        """
        try:
            import win32com.client
            import pythoncom
            
            print(f"[NotesSync] Starting synchronization for {pptx_path}")
            pythoncom.CoInitialize()
            
            ppt_app = win32com.client.DispatchEx("PowerPoint.Application")
            ppt_app.Visible = True  # Must be True - PowerPoint doesn't allow hiding
            
            abs_path = os.path.abspath(pptx_path)
            print(f"[NotesSync] Opening {abs_path}")
            presentation = ppt_app.Presentations.Open(abs_path, WithWindow=True)
            
            synced_count = 0
            for slide_no, script_text in slide_scripts.items():
                if not script_text:
                    continue
                
                try:
                    slide = presentation.Slides(slide_no)
                    notes_page = slide.NotesPage
                    
                    # Find notes placeholder
                    placeholder = None
                    try:
                        placeholder = notes_page.Shapes.Placeholders(2)
                    except:
                        # Fallback: find any text shape
                        for shp in notes_page.Shapes:
                            try:
                                if hasattr(shp, "TextFrame"):
                                    placeholder = shp
                                    break
                            except:
                                continue
                    
                    if placeholder:
                        placeholder.TextFrame.TextRange.Text = script_text
                        synced_count += 1
                        print(f"[NotesSync] Slide {slide_no}: Synced ({len(script_text)} chars)")
                    else:
                        print(f"[NotesSync] Slide {slide_no}: No placeholder found")
                
                except Exception as e:
                    print(f"[NotesSync] Slide {slide_no}: Failed - {e}")
            
            # Save and close
            presentation.Save()
            presentation.Close()
            ppt_app.Quit()
            print(f"[NotesSync] Complete - {synced_count}/{len(slide_scripts)} slides updated")
            
        except ImportError:
            print("[NotesSync] Warning: pywin32 not installed")
        except Exception as e:
            print(f"[NotesSync] Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                presentation.Close()
            except: pass
            try:
                ppt_app.Quit()
            except: pass
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except:
                pass
