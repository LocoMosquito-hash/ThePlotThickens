import re
import os

def apply_migration():
    file_path = 'app/views/gallery_widget.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    import_pattern = r'from PyQt6.QtNetwork import.*?\n'
    import_statement = 'from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply\n\nfrom app.utils.character_completer import CharacterCompleter, convert_mentions_to_char_refs\n'
    content = re.sub(import_pattern, import_statement, content)
    
    # Update QuickEventEditor initialization
    old_completer = r'# Create character tag completer\n        self\.tag_completer = CharacterTagCompleter\(self\)(.*?)self\.tag_completer\.hide\(\)'
    new_completer = '''# Create character tag completer
        self.tag_completer = CharacterCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.on_character_selected)
        self.tag_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )'''
    
    content = re.sub(old_completer, new_completer, content, flags=re.DOTALL)
    
    # Add new on_character_selected method before check_for_character_tag 
    if 'def on_character_selected(self, character_name: str):' not in content:
        on_char_selected = '''
    def on_character_selected(self, character_name: str):
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.tag_completer.insert_character_tag(character_name)
        
    '''
        content = content.replace('    def check_for_character_tag(self):', on_char_selected + '    def check_for_character_tag(self):')
    
    # Update convert_mentions_to_char_refs method to use the utility function
    convert_method = r'def convert_mentions_to_char_refs\(self, text: str\) -> str:.*?return processed_text'
    new_convert = '''def convert_mentions_to_char_refs(self, text: str) -> str:
        """Convert @mentions to [char:ID] format for storage.
        
        Args:
            text: Text with @CharacterName mentions
            
        Returns:
            Text with [char:ID] references
        """
        return convert_mentions_to_char_refs(text, self.characters)'''
    
    content = re.sub(convert_method, new_convert, content, flags=re.DOTALL)
    
    # Simplify check_for_character_tag and insert_character_tag methods as they're now handled by CharacterCompleter
    check_method = r'def check_for_character_tag\(self\):.*?# Hide the completer if we\'re not typing a tag\n        self\.tag_completer\.hide\(\)'
    new_check = '''def check_for_character_tag(self):
        """This method is now handled by CharacterCompleter."""
        pass'''
    
    content = re.sub(check_method, new_check, content, flags=re.DOTALL)
    
    insert_method = r'def insert_character_tag\(self, character_name: str\):.*?self\.text_edit\.setFocus\(\)'
    new_insert = '''def insert_character_tag(self, character_name: str):
        """This method is now handled by CharacterCompleter."""
        self.on_character_selected(character_name)'''
    
    content = re.sub(insert_method, new_insert, content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully migrated CharacterTagCompleter to CharacterCompleter in QuickEventEditor")

if __name__ == '__main__':
    apply_migration() 