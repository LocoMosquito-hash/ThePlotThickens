# Ren'Py Audio System

> **Fetched from:** https://www.renpy.org/doc/html/audio.html  
> **Date:** January 2025  
> **Purpose:** Understanding audio asset management for The Plot Thickens project

# Audio

Ren'Py supports playing music and sound effects in the background, using the following audio file formats:

- **Opus**
- **Ogg Vorbis**
- **MP3**
- **MP2**
- **FLAC**
- **WAV** (uncompressed 16-bit signed PCM only)

## Audio Channels

Ren'Py supports an arbitrary number of audio channels. There are three normal channels defined by default:

- **music** - A channel for music playback.
- **sound** - A channel for sound effects.
- **voice** - A channel for voice.

Normal channels support playing and queueing audio, but only play back one audio file at a time. New normal channels can be registered with `renpy.music.register_channel()`.

In addition to the normal channels, there is one special channel, **audio**. The audio channel supports playing back multiple audio files at one time, but does not support queueing sound or stopping playback.

The Music Volume, Sound Volume, and Voice Volume settings of the in-game preferences menu are used to set individual volumes for these channels.

## Audio Directory and Namespace

When Ren'Py searches for an audio file, it will start inside the game directory. If the provided file is not found there, it will also look in the `game/audio` directory. For example:

```renpy
play music "opening.ogg"
```

will first look for `game/opening.ogg`. If not found, Ren'Py will look for `game/audio/opening.ogg`.

### Automatic Audio Namespace

Files found in the `game/audio` directory that end with a supported extension (`.wav`, `.mp2`, `.mp3`, `.ogg`, and `.opus`) are automatically placed by Ren'Py into the audio namespace. This means that `game/audio/Town_theme.ogg` can be played with:

```renpy
play music town_theme
```

The usable name is determined by stripping the extension and forcing the rest of the filename to lower case. This only works for audio files with names that can be expressed as Python variables.

### Manual Audio Definition

When a file isn't placed automatically into the audio namespace, it can still be placed there manually with the define statement:

```renpy
define audio.sunflower = "my_music/sun-flower-slow-jam.ogg"
```

and then use:

```renpy
play music sunflower
```

## Play Statement

The play statement is the most common way to play sound and music. If a file is currently playing on a normal channel, it is interrupted and replaced with the new file.

**Basic Syntax:**

```renpy
play channel audiofile(s) [properties]
```

**Examples:**

```renpy
play music "mozart.ogg"
play sound "woof.mp3"
play myChannel "punch.wav"  # 'myChannel' needs to be defined

# Play a list of sounds or music
play music [ "a.ogg", "b.ogg" ] fadeout 1.0 fadein 1.0
```

### Play Statement Properties

**fadeout/fadein**
: Gives the fade time in seconds. If fadeout is not given, `config.fadeout_audio` is used.

**loop/noloop**
: Controls whether the music loops. If neither are given, the channel default is used.

**if_changed**
: If the given track is currently playing on the channel, the play instruction doesn't interrupt it.

**volume**
: Specifies a relative amplitude for the track, between 0.0 and 1.0.

**Examples with properties:**

```renpy
# Conditional play
label market_side:
    play music market
    "We're entering the market."

label market_main:
    play music market if_changed
    "Maybe we just entered the market, maybe we were already there."
    "If we were already there, the music didn't stop and start over."

# Volume control
play sound "woof.mp3" volume 0.5

# Fade effects
play music "background.ogg" fadein 2.0
```

### Audio Channel Multi-play

On the audio channel, multiple play statements play multiple sounds at the same time:

```renpy
play audio "sfx1.opus"
play audio "sfx2.opus"
```

### Synchronized Start

Ren'Py supports a feature that ensures audio files start playing at the same time. This feature is enabled on looping audio channels (like music) by default.

When synchro start is enabled and multiple play statements are run at the same time, the audio in each channel will start synchronized when:

- Audio files on every channel have been loaded
- All channels have been faded out

## Stop Statement

The stop statement begins with the keyword stop, followed by the name of a channel to stop sound on:

```renpy
stop sound
stop music fadeout 1.0
```

## Queue Statement

The queue statement is used to queue up audio files. They will be played when the channel finishes playing the currently playing file.

```renpy
queue sound "woof.mp3"
queue music [ "a.ogg", "b.ogg" ]

# With volume control
play sound "woof.mp3" volume 0.25
queue sound "woof.mp3" volume 0.5
queue sound "woof.mp3" volume 0.75
queue sound "woof.mp3" volume 1.0
```

When multiple queue statements are given without an interaction between them, all sound files are added to the queue. After an interaction has occurred, the first queue statement clears the queue.

---

**Key Points for The Plot Thickens:**

1. **Multi-format Support**: Wide range of audio formats supported (Opus, OGG, MP3, FLAC, WAV)
2. **Channel System**: Separate channels for music, sound, voice, plus custom channels
3. **Asset Organization**: Automatic discovery from audio/ directory with namespace creation
4. **Playback Control**: Play, stop, queue operations with fade effects
5. **Volume Management**: Per-channel and per-file volume control
6. **Synchronized Playback**: Multiple audio tracks can start simultaneously
7. **Conditional Playback**: if_changed clause prevents interrupting current tracks
8. **Queue System**: Sequential audio playback for music playlists and sound sequences

This is essential for understanding how Ren'Py projects organize and manage audio assets throughout the game.
