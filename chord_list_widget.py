"""Chord list widget - displays small chord diagrams in a scrollable area"""
from PySide6.QtWidgets import QFrame, QScrollArea, QWidget, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QSize, Signal


class SmallChordDiagram(QFrame):
    """Displays a small chord diagram"""
    
    def __init__(self, chord_name, chord_frets, parent=None, diagram_width=80, diagram_height=120, show_border=True):
        super().__init__(parent)
        self.chord_name = chord_name
        self.chord_frets = chord_frets  # List of 6 frets
        self.diagram_width = diagram_width
        self.diagram_height = diagram_height
        self.show_border = show_border
        
        self.setFixedSize(self.diagram_width, self.diagram_height)
        self._update_border_style()
    
    def set_size(self, width, height):
        """Update diagram size"""
        self.diagram_width = width
        self.diagram_height = height
        self.setFixedSize(width, height)
    
    def set_border_visible(self, visible):
        """Update border visibility"""
        self.show_border = visible
        self._update_border_style()
    
    def _update_border_style(self):
        """Update the border style based on show_border setting"""
        if self.show_border:
            self.setStyleSheet("border: 1px solid gray;")
        else:
            self.setStyleSheet("border: none;")
    
    def paintEvent(self, event):
        """Draw small chord diagram"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor(245, 245, 245))
        
        # Draw chord name at top (scale with diagram size)
        font_size = max(6, int(width / 10))
        painter.setFont(QFont('Arial', font_size, QFont.Bold))
        painter.drawText(0, 0, width, int(height * 0.15), Qt.AlignCenter, self.chord_name)
        
        # Small fretboard dimensions (scale with diagram size)
        fret_height = max(6, int(height * 0.15))
        string_width = max(8, int(width * 0.12))
        start_x = int(width * 0.1)
        start_y = int(height * 0.2)
        num_frets_to_show = 4
        
        # Draw strings (vertical lines)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for string_idx in range(6):
            x = start_x + string_idx * string_width
            painter.drawLine(x, start_y, x, start_y + num_frets_to_show * fret_height)
        
        # Draw frets (horizontal lines)
        for fret_idx in range(num_frets_to_show + 1):
            y = start_y + fret_idx * fret_height
            painter.drawLine(start_x, y, start_x + 5 * string_width, y)
        
        # Draw nut (thicker first fret line)
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawLine(start_x, start_y, start_x + 5 * string_width, start_y)
        
        # Draw chord dots
        painter.setPen(QPen(QColor(50, 100, 200), 1))
        painter.setBrush(QBrush(QColor(100, 150, 255)))
        
        if self.chord_frets:
            for string_idx, fret in enumerate(self.chord_frets):
                if fret == 0:
                    # Open string - draw circle above nut
                    x = start_x + string_idx * string_width
                    painter.drawEllipse(int(x - 3), int(start_y - 8), 6, 6)
                elif fret > 0 and fret < num_frets_to_show:
                    # Fretted string - draw dot
                    x = start_x + string_idx * string_width
                    y = start_y + fret * fret_height - fret_height // 2
                    painter.drawEllipse(int(x - 2), int(y - 2), 4, 4)
                elif fret == -1:
                    # Muted string - draw X
                    x = start_x + string_idx * string_width
                    painter.setPen(QPen(QColor(200, 0, 0), 2))
                    painter.drawLine(int(x - 3), int(start_y - 10), int(x + 3), int(start_y - 4))
                    painter.drawLine(int(x + 3), int(start_y - 10), int(x - 3), int(start_y - 4))
                    painter.setPen(QPen(QColor(50, 100, 200), 1))


class MiniChordDisplayList(QScrollArea):
    """Customizable scrollable list of mini chord diagrams
    
    This widget displays a horizontal list of small chord diagrams in a scrollable area.
    It can be customized through various properties for appearance and behavior.
    """
    
    # Signals
    chord_selected = Signal(str)  # Emitted when a chord is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Customizable properties
        self.diagram_width = 80
        self.diagram_height = 120
        self.spacing = 5
        self.border_visible = True
        self.background_color = QColor(255, 255, 255)
        self.padding = 5
        
        # Initialize widget
        self.setFixedHeight(140)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        # Container widget
        self.container = QWidget()
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        self.layout.setSpacing(self.spacing)
        self.setWidget(self.container)
        
        # Store references to diagrams for updates
        self.diagrams = []
    
    def set_diagram_size(self, width, height):
        """Set the size of individual chord diagrams"""
        self.diagram_width = width
        self.diagram_height = height
        self._refresh_diagrams()
    
    def set_spacing(self, spacing):
        """Set spacing between diagrams"""
        self.spacing = spacing
        self.layout.setSpacing(spacing)
    
    def set_padding(self, padding):
        """Set padding around the diagram list"""
        self.padding = padding
        self.layout.setContentsMargins(padding, padding, padding, padding)
    
    def set_background_color(self, color):
        """Set background color of the display"""
        self.background_color = color
        if isinstance(color, QColor):
            color_str = f"rgb({color.red()}, {color.green()}, {color.blue()})"
        else:
            color_str = color
        self.setStyleSheet(f"QScrollArea {{ border: none; background-color: {color_str}; }}")
    
    def set_border_visible(self, visible):
        """Set whether diagram borders are visible"""
        self.border_visible = visible
        self._refresh_diagrams()
    
    def set_chords(self, chords):
        """Set the list of chords to display
        
        Args:
            chords: List of TargetChord objects
        """
        # Clear existing widgets
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.diagrams = []
        
        # Add small chord diagrams
        for chord in chords:
            diagram = SmallChordDiagram(
                chord.name, 
                chord.frets,
                diagram_width=self.diagram_width,
                diagram_height=self.diagram_height,
                show_border=self.border_visible
            )
            self.diagrams.append(diagram)
            self.layout.addWidget(diagram)
        
        # Add stretch at the end
        self.layout.addStretch()
    
    def _refresh_diagrams(self):
        """Refresh all diagrams with current settings"""
        for diagram in self.diagrams:
            diagram.set_size(self.diagram_width, self.diagram_height)
            diagram.set_border_visible(self.border_visible)
            diagram.update()


class ChordListWidget(MiniChordDisplayList):
    """Backward compatible chord list widget - extends MiniChordDisplayList
    
    This class is kept for backward compatibility. New code should use MiniChordDisplayList directly.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
