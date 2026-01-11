# Guitar Fretboard MIDI Visualizer

A real-time guitar fretboard visualization app that displays chord diagrams and highlights frets as you play via MIDI.

## Features

- **Visual Fretboard**: 24-fret guitar fretboard display
- **Chord Library**: 10 common guitar chords (E, A, D, G, C, F major + Em, Am, Dm, Gm)
- **Real-time MIDI Input**: Shows frets being pressed in real-time
- **Practice Mode**: Display target chord dots while practicing
- **Standard Tuning**: Pre-configured for standard guitar tuning (E A D G B E)

## Installation

### Prerequisites
- Python 3.8+
- MIDI input device or software MIDI (e.g., loopMIDI)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python guitar_fretboard_app.py
```

## Usage

1. **Connect MIDI Input**:
   - Select your MIDI input device from the dropdown
   - Click "Connect MIDI" to start listening

2. **Select a Chord**:
   - Choose a chord from the "Practice Chord" dropdown
   - Light blue dots show the target fret positions

3. **Play**:
   - Press frets on your MIDI guitar controller
   - Red dots show currently pressed frets in real-time
   - Try to match the light blue chord dots with your red pressed notes

## Supported Chords

- E Major, A Major, D Major, G Major, C Major, F Major
- Em, Am, Dm, Gm

You can easily add more chords by modifying the `CHORD_PRESETS` dictionary in the code.

## How It Works

- **MIDI Note Mapping**: Converts MIDI note numbers to fret positions using standard guitar tuning
- **Real-time Display**: Updates fretboard as MIDI notes are received
- **Chord Visualization**: Shows practice target chords as reference

## Testing

If you don't have a MIDI guitar:
1. Install **loopMIDI** (free Windows MIDI driver)
2. Use a MIDI keyboard or sequencer software to send notes to loopMIDI
3. Select loopMIDI in the app

## Troubleshooting

- **No MIDI inputs**: Install loopMIDI or check your MIDI device drivers
- **Notes not showing**: Ensure your MIDI device is selected and connected
- **Wrong fret positions**: Verify your MIDI device is using standard tuning (E A D G B E)

## Future Enhancements

- Add more chord presets
- Support for different tunings (drop D, open G, etc.)
- Record and playback practice sessions
- Visual feedback for correct/incorrect notes
- MIDI output for tone generation
