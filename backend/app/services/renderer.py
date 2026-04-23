from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class SlideRenderer:
    """Professional UI-driven renderer for training slides."""
    
    def __init__(self, width=1280, height=720, video_title="Training Module"):
        self.width = width
        self.height = height
        self.video_title = video_title
        # Color Palette (Corporate Training)
        self.COLORS = {
            "bg": "#FFFFFF",
            "primary": "#127c96",    # Professional Navy Blue (Lighter than before)
            "accent": "#38bdf8",     # Sky Blue
            "text": "#334155",       # Slate
            "warning": "#ef4444",    # Red
            "subtle": "#f8fafc"      # Light Gray
        }
        
        # Load Professional Fonts
        try:
            self.font_title = ImageFont.truetype("arialbd.ttf", 40)   # For Intro Slide
            self.font_video_title = ImageFont.truetype("arialbd.ttf", 20) # For Header Bar
            self.font_header = ImageFont.truetype("arialbd.ttf", 20)  # For Slide Heading
            self.font_body = ImageFont.truetype("arial.ttf", 18)      # For Content
            self.font_sub = ImageFont.truetype("arial.ttf", 16)       # Small subtitles
        except:
            self.font_title = ImageFont.load_default()
            self.font_video_title = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()

    def _draw_base_template(self, draw):
        """Draw the compact branding bar and background."""
        title = self.video_title
        # Compact Branding Bar (Height reduced to 70px)
        draw.rectangle([0, 0, self.width, 70], fill=self.COLORS["primary"])
        draw.rectangle([0, 70, self.width, 74], fill=self.COLORS["accent"])
        
        # Title in Header (Repositioned for compact bar)
        header_font = self.font_video_title
        draw.text((60, 20), title, fill="#FFFFFF", font=header_font)

    def render_title_slide(self, scene_data, output_path):
        """A professional intro/title slide with multi-line wrapping."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["primary"])
        draw = ImageDraw.Draw(img)
        
        # Decorative accents
        draw.rectangle([0, self.height - 20, self.width, self.height], fill=self.COLORS["accent"])
        
        # Main Title (Wrapping Logic)
        title = scene_data["title"]
        char_width = 30 # Approx for 64pt bold
        wrap_width = max(15, (self.width - 120) // char_width)
        lines = textwrap.wrap(title, width=wrap_width)
        
        # Calculate total height of wrapped title block for centering
        line_spacing = 75
        total_text_h = len(lines) * line_spacing
        y_cursor = (self.height - total_text_h) // 2 - 40
        
        for line in lines:
            lw, lh = draw.textbbox((0, 0), line, font=self.font_title)[2:]
            draw.text(((self.width - lw) // 2, y_cursor), line, fill="#FFFFFF", font=self.font_title)
            y_cursor += line_spacing
        
        # Subtitle
        sub = "Training Module | Compliance & Quality"
        sw, sh = draw.textbbox((0, 0), sub, font=self.font_sub)[2:]
        draw.text(((self.width - sw) // 2, y_cursor + 40), sub, fill=self.COLORS["accent"], font=self.font_sub)
        
        img.save(output_path)
        return output_path

    def render_training_slide(self, scene_data, output_path):
        """LMS-style slide with text auto-scaling to fit content."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["bg"])
        draw = ImageDraw.Draw(img)
        
        self._draw_base_template(draw)
        
        # 0. Slide Heading
        slide_title = scene_data["title"]
        char_width = 25
        wrap_width = max(15, (self.width - 150) // char_width)
        title_lines = textwrap.wrap(slide_title, width=wrap_width)
        
        y_offset = 100
        for line in title_lines:
            draw.text((60, y_offset), line, fill=self.COLORS["primary"], font=self.font_header)
            y_offset += 40
        
        y_offset += 15
        bullets = scene_data.get("bullets", [])
        
        # 1. Fixed Layout (No scaling loop as requested)
        line_height = 32
        wrap_width = 110
        
        # 2. Render
        for bullet in bullets:
            # Bullet icon
            draw.ellipse([60, y_offset + 8, 72, y_offset + 20], fill=self.COLORS["accent"])
            
            wrapped = textwrap.wrap(bullet, width=wrap_width)
            for line in wrapped:
                draw.text((100, y_offset), line, fill=self.COLORS["text"], font=self.font_body)
                y_offset += line_height
            y_offset += 15
            
        img.save(output_path)
        return output_path

        img.save(output_path)
        return output_path

    def render_table_slide(self, scene_data, output_path):
        """Professional data table renderer."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["bg"])
        draw = ImageDraw.Draw(img)
        self._draw_base_template(draw)
        
        table_data = scene_data["tables"][0] if scene_data["tables"] else []
        if not table_data:
            draw.text((100, 300), "No table data available", fill='red', font=self.font_body)
        else:
            x_start, y_start = 100, 150
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
