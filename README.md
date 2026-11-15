## Inspiration

## What it does

## How we built it

## Challenges we ran into

## Accomplishments that we're proud of

## What we learned

## What's next for BeatBuddy


# BeatBuddy: Composing a Conversation Between Conductor and Orchestra
## Inspiration
Conducting is a nuanced art that requires years of experience to perfect, but practice can be difficult without an orchestra available to respond to gestures in a natural way.

We wanted to connect two things that do not usually interact: a conductor’s physical movement and responsive audio playback.

BeatBuddy turns a webcam into a practice partner. Instead of asking a musician to adapt to a fixed metronome, it listens to their conducting and adapts the music to them in real time.

## What We Built
BeatBuddy is a real-time conducting practice application that:

- Tracks a conductor’s index fingertip through a webcam.
- Recognizes downbeats from the shape and direction of hand movement.
- Estimates conducting tempo from the time between gestures.
- Adjusts music playback speed to match the live tempo.
- Provides visual and audio metronome cues.
- Displays live tempo and playback-rate feedback.
- Changes volume based on the energy of the conductor’s movement.
- Includes a searchable classical music library to provide conductors with information about repertoire
- Can add visual feedback when the conductor is substantially ahead of or behind the selected piece.
The result is an interactive rehearsal environment.

### The Technology Behind the Gesture
The computer-vision pipeline begins with each camera frame being processed by OpenCV and MediaPipe Hand Landmarker. We track one hand and extract landmark 8, the index fingertip.

Raw camera coordinates can be noisy, so we applied smoothing:

[
p_t = \alpha r_t + (1-\alpha)p_{t-1}
]
where (r_t) is the raw fingertip position, (p_t) is the filtered position, and (\alpha) controls how quickly the system responds.

The fingertip trajectory is then interpreted as a conducting gesture:

- Detect downward movement.
- Measure the size of the stroke.
- Detect the reversal as the hand moves upward.
- Treat a sufficiently large reversal as a downbeat.
- Reject tiny movements and duplicate detections using a dead zone, minimum stroke threshold, and cooldown period.
- Tempo is estimated from recent downbeat intervals:

[
\text{tempo} = \frac{60}{\text{average interval in seconds}}
]
A short rolling history makes the result more stable while still allowing the system to respond to changes in conducting speed.

### Adaptive Audio
Once BeatBuddy detects the live tempo, it maps it to a playback rate relative to the selected piece:

[
\text{target rate} =
\frac{\text{live tempo}}{\text{reference tempo}}
]

Playback is constrained to a practical range and adjusted gradually to avoid jumps in audio.
The same idea powers dynamic volume. Larger, more expressive gestures increase the target volume, while smaller gestures reduce it. Volume transitions are smoothed over the duration of a beat, creating a connection between physical expression and musical intensity.

### Composition as a Design Principle
The theme of composition shaped both the technology and the experience.

A musical composition is built from relationships: beat and silence, movement and stillness, individual parts and the whole ensemble. BeatBuddy applies the same principle to software:

Camera input becomes movement.
Movement becomes gesture.
Gesture becomes tempo.
Tempo becomes playback.
Playback becomes feedback.
Feedback changes the next gesture.
This creates a continuous loop between human intention and machine response.

We were especially interested in composing a new kind of duet: one performer and one computer. The user supplies interpretation and expression; BeatBuddy supplies timing, audio, and reflection.

## Learning Through the Build
We learned that real-time interaction requires much more than detecting an object successfully.

A technically accurate hand tracker can still feel unusable if it:

Reacts to jitter.
Misses a beat during a reversal.
Changes tempo too aggressively.
Produces feedback that is delayed or confusing.
We learned to think in terms of perceptual latency, not only computational latency. Smoothing, cooldowns, rolling averages, gradual playback-rate changes, and visual countdowns all help the system feel predictable to a human performer.

We also learned that musical data matters. The music library is not just a collection of audio files: metadata such as composer, work, BPM, beats per bar, and artwork helps turn practice into exploration and learning.

## Challenges
### Recognizing a Beat from Imperfect Movement
Conducting gestures are expressive rather than mechanically identical. Different people use different sizes, speeds, and styles of movement.

We addressed this by focusing on the broad shape of a gesture rather than requiring an exact path. A downbeat is recognized through a substantial downward stroke followed by a reversal, while small movements are ignored.

### Stabilizing Computer Vision
Webcam footage contains jitter, changing lighting, and moments when the hand disappears. We used fingertip smoothing and temporary trail persistence to avoid making the interface flicker or lose context immediately.
We also render a curved fingertip trail using interpolation, making the detected movement easier to understand visually.

### Keeping Audio Musical
Instantly changing playback speed can sound unnatural. We limited the allowed playback range and capped how quickly the rate can change. This lets the audio follow the conductor without sounding as if it is constantly being manipulated.

### Synchronizing Multiple Feedback Systems
Audio playback, camera frames, countdown animation, metronome clicks, visual effects, and the PyQt interface all run on different timing mechanisms.
We had to coordinate them carefully so that the user receives consistent feedback. A countdown based on beats-per-minute prepares the user before playback begins, while an ongoing visual metronome reinforces the pulse during rehearsal.

## Novel Ideas
A Metronome That Listens
Traditional metronomes impose time. BeatBuddy reverses that relationship: it listens to the conductor and reshapes playback around their timing.

## Movement as Musical Dynamics
The conductor’s movement is not treated only as a binary “on beat” or “off beat” signal. Gesture energy also influences volume, connecting physical expression to the sound being practiced.

## Feedback That Teaches Without Interrupting
BeatBuddy does not stop the music whenever the user drifts. Instead, it shows live tempo, playback rate, and optional visual effects indicating whether the conductor is moving unusually fast or slowly. This encourages self-correction while preserving flow.

## Connecting Practice and Discovery
The music library connects conducting mechanics with musical knowledge. Users can select pieces, see their metadata, learn about composers and works, and immediately practice them with responsive audio.

## Improving the World by Connecting Things That Usually Aren’t
BeatBuddy connects:

Solo practice with ensemble-like feedback.
Computer vision with musical interpretation.
Physical movement with audio dynamics.
Technical measurement with creative expression.
Music education with accessible consumer hardware.
Classical music discovery with interactive technology.
A conductor should not need access to a full orchestra to practice responding to tempo. A student should not need expensive equipment to receive meaningful feedback. A webcam, a computer, and a piece of music can become the beginning of an intelligent rehearsal space.

## Looking Forward
Future versions could distinguish between hands, provide score-aware feedback, and learn a user’s personal conducting style over time.

The long-term goal is not to replace teachers or musicians. It is to make the space between lessons, rehearsals, and performances more useful.

BeatBuddy began with a simple question:

What if the music could follow the conductor, instead of the conductor always following the music?

Our answer is a composition made from movement, timing, technology, and human expression.
