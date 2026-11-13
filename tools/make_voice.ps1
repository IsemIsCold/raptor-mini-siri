param([string]$OutDir)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Zira Desktop")
$s.Rate = 1
New-Item -ItemType Directory -Force $OutDir | Out-Null
$clips = [ordered]@{
  "welcome"   = "Hi, I am Mini Siri! Ask me the time, the date, a joke, or some maths."
  "math"      = "Here is your answer."
  "mathneed"  = "Give me two whole numbers, for example, twelve times seven."
  "mathop"    = "Should I add, subtract, multiply or divide?"
  "divzero"   = "I cannot divide by zero!"
  "time"      = "Here is the time."
  "date"      = "Here is today's date."
  "joke1"     = "Why did the flowchart go to therapy? It had too many unresolved loops."
  "joke2"     = "I would tell you a U D P joke, but you might not get it."
  "joke3"     = "Why do programmers prefer dark mode? Because light attracts bugs."
  "joke4"     = "There are ten kinds of people: those who understand binary, and those who don't."
  "greet1"    = "Hello! How can I help you?"
  "greet2"    = "Hi there! Ask me the time, a joke, or some maths."
  "greet3"    = "Hey! What can I do for you?"
  "about"     = "I am Mini Siri, an assistant built entirely as a RAPTOR flowchart."
  "howareyou" = "I am doing great. All my loops are running smoothly!"
  "thanks"    = "You are welcome!"
  "bye"       = "Goodbye! Thanks for chatting."
  "heads"     = "I flipped a coin. Heads!"
  "tails"     = "I flipped a coin. Tails!"
  "teach"     = "Sorry, I do not know that one yet. Teach me! Which category is it?"
  "never"     = "OK, never mind."
  "didnt"     = "Sorry, I did not catch that."
}
foreach ($k in $clips.Keys) {
  $s.SetOutputToWaveFile((Join-Path $OutDir "siri_$k.wav"))
  $s.Speak($clips[$k])
}
for ($i = 1; $i -le 6; $i++) {
  $s.SetOutputToWaveFile((Join-Path $OutDir "siri_dice$i.wav"))
  $s.Speak("I rolled a dice. It is a $i!")
}
$s.SetOutputToNull()
(Get-ChildItem $OutDir -Filter "siri_*.wav").Count
