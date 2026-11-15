## Inspiration
Conducting is a nuanced art that requires years of experience to perfect, but practice can be difficult without an orchestra available to react to gestures in a natural way.

We wanted to connect a conductor’s physical movement to responsive audio playback, creating a novel space for musicians to enjoy each other's compositions even when they cannot be present together.

## What it does

BeatBuddy is an interactive rehearsal environment that:

- Tracks a conductor’s movements through a webcam
- Recognizes downbeats and estimates tempo
- Adjusts music playback speed to match the conducting
- Changes volume based on the energy of gestures
- Provides visual feedback and metronome queues
- Includes a searchable classical music library to provide information about repertoire

## How we built it

We built BeatBuddy using Python, OpenCV, MediaPipe, and PyQt.

MediaPipe tracks the position of the conductor's index finger, which we smooth to reduce camera noise. We then analyse the movement to identify downbeats by looking for large downward strokes followed by a change in direction.

Tempo is calculated from the timing between recent downbeats, and this tempo is used to adjust audio playback in real time. We also use gesture size to control playback volume, allowing conductors to shape the music naturally through movement.

## Challenges we ran into

One of the biggest challenges was recognising conducting gestures reliably. Everyone conducts slightly differently, so we needed an approach that could identify beats without requiring identical movements every time.

It was also difficult to keep audio changes smooth enough to sound musical. Synchronising the vision system, audio playback, metronome, and user interface was another significant challenge.

## Accomplishments that we're proud of

- Great tean communication, allowing us to effectively draw on individual strengths
- Combining music, computer vision, and audio processing in a novel way
- Creating a polished application that fits the overall hackathon theme

## What we learned

Neither of us had built any kind of computer vision system before, so we both learnt how to deal with unreliable input and how to analyse it to extract required features.

From asking other hackathon participants to test our application we also learnt the importance of a good user interface.

## What's next for BeatBuddy

We intend to add support for two\-handed conducting by tracking other MediaPipe hand landmarks. This would allow for analysis of more complex conducting gestures, so that BeatBuddy can better support more able conductors.

We would also like to expand the library to include pieces with more complex time signature changes. This might necessitate a 'beat map' be stored with each piece, detailing how the time between beats changes throughout.
