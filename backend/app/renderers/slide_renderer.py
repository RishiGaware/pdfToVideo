from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class SlideRenderer:
    """Professional UI-driven renderer for training slides."""
    
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        # Color Palette (Corporate Training)
        self.COLORS = {
            "bg": "#FFFFFF",
            "primary": "#0f172a",    # Dark Slate
            "accent": "#38bdf8",     # Sky Blue
            "text": "#334155",       # Slate
            "warning": "#ef4444",    # Red
            "subtle": "#f8fafc"      # Light Gray
        }
        
        # Load Professional Fonts
        try:
            self.font_title = ImageFont.truetype("arialbd.ttf", 64)
            self.font_header = ImageFont.truetype("arialbd.ttf", 48)
            self.font_body = ImageFont.truetype("arial.ttf", 36)
            self.font_sub = ImageFont.truetype("arial.ttf", 28)
        except:
            self.font_title = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()

    def _draw_base_template(self, draw, title):
        """Draw the common branding bar and background."""
        # Branding Bar
        draw.rectangle([0, 0, self.width, 100], fill=self.COLORS["primary"])
        draw.rectangle([0, 100, self.width, 105], fill=self.COLORS["accent"])
        
        # Title in Header
        draw.text((60, 25), title[:50], fill="#FFFFFF", font=self.font_header)

    def render_title_slide(self, scene_data, output_path):
        """A professional intro/title slide."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["primary"])
        draw = ImageDraw.Draw(img)
        
        # Decorative accents
        draw.rectangle([0, self.height - 20, self.width, self.height], fill=self.COLORS["accent"])
        
        # Main Title
        title = scene_data["title"]
        w, h = draw.textbbox((0, 0), title, font=self.font_title)[2:]
        draw.text(((self.width - w) // 2, (self.height - h) // 2 - 40), title, fill="#FFFFFF", font=self.font_title)
        
        # Subtitle
        sub = "Training Module | Compliance & Quality"
        sw, sh = draw.textbbox((0, 0), sub, font=self.font_sub)[2:]
        draw.text(((self.width - sw) // 2, (self.height - h) // 2 + 80), sub, fill=self.COLORS["accent"], font=self.font_sub)
        
        img.save(output_path)
        return output_path

    def render_training_slide(self, scene_data, output_path):
        """LMS-style slide with text auto-scaling to fit content."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["bg"])
        draw = ImageDraw.Draw(img)
        
        self._draw_base_template(draw, scene_data["title"])
        bullets = scene_data.get("bullets", [])
        
        # 1. Scaling Logic: Find the best font size
        current_font = self.font_body # Default 36pt
        line_height = 50
        
        def calculate_height(font, lh):
            h = 0
            for b in bullets:
                wrapped = textwrap.wrap(b, width=65 if font == self.font_body else 80)
                h += len(wrapped) * lh + 30
            return h

        total_h = calculate_height(current_font, line_height)
        if total_h > 520: # Exceeds body area
            current_font = self.font_sub # Switch to 28pt
            line_height = 40
            total_h = calculate_height(current_font, line_height)

        # 2. Render
        y_offset = 150 + ((520 - total_h) // 2) if total_h < 520 else 150
        
        for bullet in bullets:
            draw.ellipse([60, y_offset + 10, 75, y_offset + 25], fill=self.COLORS["accent"])
            wrapped = textwrap.wrap(bullet, width=65 if current_font == self.font_body else 80)
            for line in wrapped:
                draw.text((100, y_offset), line, fill=self.COLORS["text"], font=current_font)
                y_offset += line_height
            y_offset += 25
            
        img.save(output_path)
        return output_path

    def render_warning_slide(self, scene_data, output_path):
        """Critical/Warning slide with red highlights."""
        img = Image.new('RGB', (self.width, self.height), color="#fff1f2") # Very light red bg
        draw = ImageDraw.Draw(img)
        
        # Warning Header
        draw.rectangle([0, 0, self.width, 100], fill=self.COLORS["warning"])
        draw.text((60, 25), "CRITICAL POINT", fill="#FFFFFF", font=self.font_header)
        
        # Body
        title = scene_data["title"]
        draw.text((60, 150), title, fill=self.COLORS["warning"], font=self.font_header)
        
        y_offset = 250
        for bullet in scene_data.get("bullets", []):
            draw.text((100, y_offset), f"! {bullet}", fill=self.COLORS["text"], font=self.font_body)
            y_offset += 60
            
        img.save(output_path)
        return output_path

    def render_table_slide(self, scene_data, output_path):
        """Professional data table renderer."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["bg"])
        draw = ImageDraw.Draw(img)
        self._draw_base_template(draw, scene_data["title"])
        
        table_data = scene_data["tables"][0] if scene_data["tables"] else []
        if not table_data:
            draw.text((100, 300), "No table data available", fill='red', font=self.font_body)
        else:
            x_start, y_start = 100, 180
            col_width = (self.width - 200) // len(table_data[0]) if table_data[0] else 100
            
            for row_idx, row in enumerate(table_data[:10]):
                y = y_start + row_idx * 50
                # Header row bg
                if row_idx == 0:
                    draw.rectangle([x_start-10, y, self.width-90, y+50], fill=self.COLORS["subtle"])
                
                for col_idx, cell in enumerate(row):
                    x = x_start + col_idx * col_width
                    cell_text = str(cell)[:25]
                    draw.text((x, y+5), cell_text, fill=self.COLORS["primary"] if row_idx == 0 else self.COLORS["text"], 
                              font=self.font_body if row_idx == 0 else self.font_body)
                    draw.line((x, y, x, y+50), fill="#cbd5e1", width=1)
                
                draw.line((x_start-10, y+50, self.width-90, y+50), fill="#cbd5e1", width=1)

        img.save(output_path)
        return output_path
