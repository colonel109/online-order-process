from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QCompleter
from PySide6.QtCore import Qt

class ProductAutoCompleter(QStyledItemDelegate):
    def __init__(self, suggestion_list, parent=None):
        super().__init__(parent)
        self.suggestion_list = suggestion_list

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)

        completer = QCompleter(self.suggestion_list, editor)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        popup = completer.popup()
        popup.setMinimumWidth(600)
        
        completer.setPopup(popup)

        editor.setCompleter(completer)
        return editor
    
    def setModelData(self, editor, model, index):
        text = editor.text()

        model.setData(index, text, Qt.ItemDataRole.EditRole)