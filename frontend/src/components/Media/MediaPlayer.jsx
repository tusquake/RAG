import { forwardRef, useRef, useImperativeHandle, useState, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react'
import './MediaPlayer.css'

const MediaPlayer = forwardRef(({ src, type, onTimeUpdate }, ref) => {
    const mediaRef = useRef(null)
    const [playing, setPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [duration, setDuration] = useState(0)
    const [muted, setMuted] = useState(false)
    const [volume, setVolume] = useState(1)

    useImperativeHandle(ref, () => ({
        seekTo: (seconds) => {
            if (mediaRef.current) {
                mediaRef.current.currentTime = seconds
                if (!playing) {
                    mediaRef.current.play()
                    setPlaying(true)
                }
            }
        },
        getCurrentTime: () => mediaRef.current?.currentTime || 0
    }))

    useEffect(() => {
        const media = mediaRef.current
        if (!media) return

        const handleTimeUpdate = () => {
            setCurrentTime(media.currentTime)
            onTimeUpdate?.(media.currentTime)
        }

        const handleLoadedMetadata = () => {
            setDuration(media.duration)
        }

        const handleEnded = () => {
            setPlaying(false)
        }

        media.addEventListener('timeupdate', handleTimeUpdate)
        media.addEventListener('loadedmetadata', handleLoadedMetadata)
        media.addEventListener('ended', handleEnded)

        return () => {
            media.removeEventListener('timeupdate', handleTimeUpdate)
            media.removeEventListener('loadedmetadata', handleLoadedMetadata)
            media.removeEventListener('ended', handleEnded)
        }
    }, [onTimeUpdate])

    function togglePlay() {
        if (mediaRef.current) {
            if (playing) {
                mediaRef.current.pause()
            } else {
                mediaRef.current.play()
            }
            setPlaying(!playing)
        }
    }

    function toggleMute() {
        if (mediaRef.current) {
            mediaRef.current.muted = !muted
            setMuted(!muted)
        }
    }

    function handleVolumeChange(e) {
        const value = parseFloat(e.target.value)
        setVolume(value)
        if (mediaRef.current) {
            mediaRef.current.volume = value
            setMuted(value === 0)
        }
    }

    function handleSeek(e) {
        const value = parseFloat(e.target.value)
        setCurrentTime(value)
        if (mediaRef.current) {
            mediaRef.current.currentTime = value
        }
    }

    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00'
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    function toggleFullscreen() {
        if (mediaRef.current && type === 'video') {
            if (document.fullscreenElement) {
                document.exitFullscreen()
            } else {
                mediaRef.current.requestFullscreen()
            }
        }
    }

    return (
        <div className="media-player">
            {type === 'video' ? (
                <video
                    ref={mediaRef}
                    src={src}
                    className="media-element video"
                    onClick={togglePlay}
                />
            ) : (
                <audio ref={mediaRef} src={src} className="media-element audio" />
            )}

            <div className="media-controls">
                <button onClick={togglePlay} className="control-btn play-btn">
                    {playing ? <Pause size={18} /> : <Play size={18} />}
                </button>

                <span className="time-display">
                    {formatTime(currentTime)} / {formatTime(duration)}
                </span>

                <input
                    type="range"
                    min="0"
                    max={duration || 0}
                    value={currentTime}
                    onChange={handleSeek}
                    className="progress-bar"
                />

                <div className="volume-control">
                    <button onClick={toggleMute} className="control-btn">
                        {muted || volume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
                    </button>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={muted ? 0 : volume}
                        onChange={handleVolumeChange}
                        className="volume-bar"
                    />
                </div>

                {type === 'video' && (
                    <button onClick={toggleFullscreen} className="control-btn">
                        <Maximize size={16} />
                    </button>
                )}
            </div>
        </div>
    )
})

MediaPlayer.displayName = 'MediaPlayer'

export default MediaPlayer
