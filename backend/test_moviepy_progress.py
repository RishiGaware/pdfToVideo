from moviepy import ColorClip
from proglog import ProgressBarLogger

class DiagnosticLogger(ProgressBarLogger):
    def callback(self, **changes):
        bars = self.state.get('bars', {})
        if bars:
            print(f"Active bars: {list(bars.keys())}")
            for name, bar in bars.items():
                print(f"  Bar '{name}': {bar.get('index')}/{bar.get('total')}")

if __name__ == "__main__":
    try:
        clip = ColorClip(size=(100,100), color=(0,0,0), duration=1)
        clip.write_videofile('test_diag.mp4', fps=10, logger=DiagnosticLogger())
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")
