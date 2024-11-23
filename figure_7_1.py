# begin figure_7_1.py

import svgwrite

def create_interface_diagram(filename="quantum_interface_diagram.svg", width=800, height=300):
    # Create SVG document
    dwg = svgwrite.Drawing(filename, size=(width, height))
    
    # Define styles
    styles = {
        'box': {
            'stroke': '#000000',
            'stroke_width': '2',
            'fill': 'none',
            'rx': '10',
            'ry': '10'
        },
        'text': {
            'font_family': 'Arial',
            'font_size': '16px',
            'text_anchor': 'middle'
        },
        'title': {
            'font_family': 'Arial',
            'font_size': '18px',
            'font_weight': 'bold',
            'text_anchor': 'middle'
        },
        'bullet': {
            'font_family': 'Arial',
            'font_size': '14px'
        },
        'arrow': {
            'stroke': '#000000',
            'stroke_width': '2',
            'marker_end': 'url(#arrow)',
            'fill': 'none'
        }
    }
    
    # Define arrow marker
    marker = dwg.marker(insert=(10, 6), size=(10, 10), orient='auto')
    marker.add(dwg.path(d='M0,0 L0,12 L10,6 z', fill='#000000'))
    dwg.defs.add(marker)
    
    # Box dimensions and positions
    box_width = 200
    box_height = 150
    box_spacing = 80
    start_x = 50
    start_y = 80
    
    # Create boxes
    boxes = []
    titles = ["Quantum Layer", "Interface Layer", "Classical Layer"]
    for i in range(3):
        x = start_x + i * (box_width + box_spacing)
        box = dwg.rect((x, start_y), (box_width, box_height), **styles['box'])
        boxes.append(box)
        dwg.add(box)
        
        # Add title
        title = dwg.text(titles[i], 
                        insert=(x + box_width/2, start_y - 20),
                        **styles['title'])
        dwg.add(title)
    
    # Add content for each box
    content = [
        ["• Superposition", "• Entanglement", "• Tunneling"],
        ["• Measurement", "• Decoherence", "• Amplification"],
        ["• Action", "• Potentials", "• Firing"]
    ]
    
    for i, box_content in enumerate(content):
        x = start_x + i * (box_width + box_spacing)
        for j, text in enumerate(box_content):
            y = start_y + 50 + j * 30
            dwg.add(dwg.text(text, 
                           insert=(x + 20, y),
                           **styles['bullet']))
    
    # Add arrows between boxes
    for i in range(2):
        x1 = start_x + (i+1) * box_width + i * box_spacing
        x2 = x1 + box_spacing
        y = start_y + box_height/2
        
        # Draw double-headed arrow
        arrow_path = f'M {x1} {y} L {x2} {y}'
        dwg.add(dwg.path(d=arrow_path, **styles['arrow']))
        
        # Draw arrowhead for opposite direction
        arrow_path_back = f'M {x2} {y} L {x1} {y}'
        dwg.add(dwg.path(d=arrow_path_back, **styles['arrow']))
    
    # Save the SVG file
    dwg.save()

if __name__ == "__main__":
    create_interface_diagram()

# end figure_7_1.py