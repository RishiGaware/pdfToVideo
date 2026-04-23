from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
import math

class SlideRenderer:
    """Professional UI-driven renderer for training slides."""
    
    def __init__(self, width=1280, height=720, video_title="Training Module"):
        self.width = width
        self.height = height
        self.video_title = video_title
        # Color Palette (Corporate Training)
        self.COLORS = {
            "bg": "#FFFFFF",
            "primary": "#127c96",
            "accent": "#38bdf8",
            "text": "#334155",
            "warning": "#ef4444",
            "subtle": "#f8fafc",
            "table_header": "#0e6377",
            "table_alt": "#f0f9ff",
            "table_border": "#cbd5e1"
        }
        
        # Load Professional Fonts
        try:
            self.font_title = ImageFont.truetype("arialbd.ttf", 40)
            self.font_video_title = ImageFont.truetype("arialbd.ttf", 20)
            self.font_header = ImageFont.truetype("arialbd.ttf", 20)
            self.font_body = ImageFont.truetype("arial.ttf", 18)
            self.font_sub = ImageFont.truetype("arial.ttf", 16)
            self.font_table_header = ImageFont.truetype("arialbd.ttf", 13)
            self.font_table_cell = ImageFont.truetype("arial.ttf", 12)
        except:
            self.font_title = ImageFont.load_default()
            self.font_video_title = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()
            self.font_table_header = ImageFont.load_default()
            self.font_table_cell = ImageFont.load_default()

    def _draw_base_template(self, draw):
        """Draw the compact branding bar and background."""
        title = self.video_title
        draw.rectangle([0, 0, self.width, 70], fill=self.COLORS["primary"])
        draw.rectangle([0, 70, self.width, 74], fill=self.COLORS["accent"])
        header_font = self.font_video_title
        draw.text((60, 20), title, fill="#FFFFFF", font=header_font)

    def render_title_slide(self, scene_data, output_path):
        """A professional intro/title slide with multi-line wrapping."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["primary"])
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([0, self.height - 20, self.width, self.height], fill=self.COLORS["accent"])
        
        title = scene_data["title"]
        char_width = 30
        wrap_width = max(15, (self.width - 120) // char_width)
        lines = textwrap.wrap(title, width=wrap_width)
        
        line_spacing = 75
        total_text_h = len(lines) * line_spacing
        y_cursor = (self.height - total_text_h) // 2 - 40
        
        for line in lines:
            lw, lh = draw.textbbox((0, 0), line, font=self.font_title)[2:]
            draw.text(((self.width - lw) // 2, y_cursor), line, fill="#FFFFFF", font=self.font_title)
            y_cursor += line_spacing
        
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
        
        line_height = 24
        wrap_width = 110
        
        for bullet in bullets:
            # Subheading lines (▸ prefix) get no bullet dot, rendered as bold labels
            if bullet.startswith("▸"):
                wrapped = textwrap.wrap(bullet, width=wrap_width)
                for line in wrapped:
                    draw.text((60, y_offset), line, fill=self.COLORS["primary"], font=self.font_header)
                    y_offset += line_height + 2
                y_offset += 4
            else:
                draw.ellipse([60, y_offset + 5, 70, y_offset + 15], fill=self.COLORS["accent"])
                
                wrapped = textwrap.wrap(bullet, width=wrap_width)
                for line in wrapped:
                    draw.text((100, y_offset), line, fill=self.COLORS["text"], font=self.font_body)
                    y_offset += line_height
                y_offset += 6
            
        img.save(output_path)
        return output_path

    def _calc_col_widths(self, table_data, total_width):
        """Calculate proportional column widths based on max content length per column."""
        num_cols = len(table_data[0]) if table_data else 0
        if num_cols == 0: return []
        
        # Measure max content length per column
        col_max_len = [0] * num_cols
        for row in table_data:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_max_len[i] = max(col_max_len[i], len(str(cell or "")))
        
        # Proportional widths with a minimum
        total_len = max(sum(col_max_len), 1)
        min_col = 60
        available = total_width - (min_col * num_cols)
        
        widths = []
        for length in col_max_len:
            w = min_col + int((length / total_len) * available)
            widths.append(w)
        
        # Adjust to fit exactly
        diff = total_width - sum(widths)
        if widths:
            widths[-1] += diff
        return widths

    def _wrap_cell(self, text, max_width, font, draw):
        """Word-wrap cell text to fit within pixel width, return list of lines."""
        text = str(text or "").strip()
        if not text: return [""]
        
        # Estimate chars per line based on font metrics
        avg_char_w = draw.textbbox((0, 0), "M", font=font)[2]
        chars_per_line = max(5, int(max_width / max(avg_char_w, 1)))
        
        return textwrap.wrap(text, width=chars_per_line) or [""]

    def _calc_row_height(self, row, col_widths, font, draw, cell_padding=4, line_h=16):
        """Calculate the height needed for a row based on wrapped content."""
        max_lines = 1
        num_cols = len(col_widths)
        for i, cell in enumerate(row):
            if i >= num_cols: break
            wrapped = self._wrap_cell(cell, col_widths[i] - 10, font, draw)
            max_lines = max(max_lines, len(wrapped))
        return max_lines * line_h + cell_padding * 2

    def render_table_slide(self, scene_data, output_path):
        """Professional auto-sizing table renderer with word-wrap and grid lines."""
        img = Image.new('RGB', (self.width, self.height), color=self.COLORS["bg"])
        draw = ImageDraw.Draw(img)
        self._draw_base_template(draw)
        
        # Slide heading
        slide_title = scene_data.get("title", "Data Table")
        title_lines = textwrap.wrap(slide_title, width=50)
        y_offset = 90
        for line in title_lines:
            draw.text((50, y_offset), line, fill=self.COLORS["primary"], font=self.font_header)
            y_offset += 28
        y_offset += 8
        
        table_data = scene_data["tables"][0] if scene_data.get("tables") else []
        if not table_data:
            draw.text((100, 300), "No table data available", fill='red', font=self.font_body)
            img.save(output_path)
            return output_path
        
        # Layout constants
        x_margin = 40
        table_width = self.width - (x_margin * 2)
        max_y = self.height - 30
        line_h = 16
        cell_pad = 5
        
        col_widths = self._calc_col_widths(table_data, table_width)
        num_cols = len(col_widths)
        
        for row_idx, row in enumerate(table_data):
            is_header = (row_idx == 0)
            font = self.font_table_header if is_header else self.font_table_cell
            
            row_h = self._calc_row_height(row, col_widths, font, draw, cell_pad, line_h)
            row_h = max(row_h, 24)
            
            # Check if row fits, stop if not
            if y_offset + row_h > max_y:
                # Draw a "continued..." indicator
                draw.text((x_margin + 10, y_offset + 2), "... (table continues)",
                          fill=self.COLORS["text"], font=self.font_sub)
                break
            
            # Row background
            if is_header:
                draw.rectangle([x_margin, y_offset, x_margin + table_width, y_offset + row_h],
                               fill=self.COLORS["table_header"])
            elif row_idx % 2 == 0:
                draw.rectangle([x_margin, y_offset, x_margin + table_width, y_offset + row_h],
                               fill=self.COLORS["table_alt"])
            
            # Draw cells
            x_cursor = x_margin
            for col_idx in range(num_cols):
                cell_text = row[col_idx] if col_idx < len(row) else ""
                cw = col_widths[col_idx]
                
                # Wrap and draw text lines
                wrapped = self._wrap_cell(cell_text, cw - 10, font, draw)
                text_color = "#FFFFFF" if is_header else self.COLORS["text"]
                
                cy = y_offset + cell_pad
                for line in wrapped:
                    draw.text((x_cursor + 5, cy), line, fill=text_color, font=font)
                    cy += line_h
                
                # Vertical grid line
                draw.line([x_cursor, y_offset, x_cursor, y_offset + row_h],
                          fill=self.COLORS["table_border"], width=1)
                x_cursor += cw
            
            # Right edge + bottom grid line
            draw.line([x_margin + table_width, y_offset, x_margin + table_width, y_offset + row_h],
                      fill=self.COLORS["table_border"], width=1)
            draw.line([x_margin, y_offset + row_h, x_margin + table_width, y_offset + row_h],
                      fill=self.COLORS["table_border"], width=1)
            
            # Top border for first row
            if row_idx == 0:
                draw.line([x_margin, y_offset, x_margin + table_width, y_offset],
                          fill=self.COLORS["table_border"], width=1)
            
            y_offset += row_h

        img.save(output_path)
        return output_path
