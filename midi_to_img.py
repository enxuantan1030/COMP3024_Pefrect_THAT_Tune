import mido
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import colorConverter

# inherit the origin mido class
class MidiFile(mido.MidiFile):

    def draw_roll_and_save(self, filename):
        roll = self.get_roll()

        plt.ioff()
        fig = plt.figure(figsize=(30, 10))
        a1 = fig.add_subplot(111)
        a1.axis("equal")
        a1.set_facecolor("black")

        # Change unit of the time axis from tick to second
        tick = self.get_total_ticks()
        second = mido.tick2second(tick, self.ticks_per_beat, self.get_tempo())
        print(f"sec: {second}")
        # Define the desired number of intervals to display on the x-axis
        desired_intervals = 20

        # Calculate the period between x-axis labels adaptively based on the MIDI file duration
        x_label_period_sec = second / desired_intervals  # Divide the duration by the desired number of intervals
        print(f"x label period second: {x_label_period_sec}")

        # Calculate the corresponding tick interval based on the adjusted x_label_period_sec
        x_label_interval = mido.second2tick(x_label_period_sec, self.ticks_per_beat, self.get_tempo()) / self.sr
        print(f"x label interval: {x_label_interval}")

        # Generate ticks and labels covering the entire duration of the MIDI file
        plt.xticks(
            [int(x * x_label_interval) for x in range(int(second / x_label_period_sec) + 1)],
            [round(x * x_label_period_sec, 2) for x in range(int(second / x_label_period_sec) + 1)]
        )

        # Change scale and label of the y-axis
        plt.yticks([y * 16 for y in range(8)], [y * 16 for y in range(8)])

        # Set empty ticks for x-axis
        a1.set_xticks([])
        a1.set_xticklabels([])

        # Set empty ticks for y-axis
        a1.set_yticks([])
        a1.set_yticklabels([])

        # Build colors
        channel_nb = 16
        transparent = colorConverter.to_rgba('black')
        colors = [mpl.colors.to_rgba(mpl.colors.hsv_to_rgb((i / channel_nb, 1, 1)), alpha=1) for i in range(channel_nb)]
        cmaps = [mpl.colors.LinearSegmentedColormap.from_list('my_cmap', [transparent, colors[i]], 128) for i in
                 range(channel_nb)]

        # Build color maps
        for i in range(channel_nb):
            cmaps[i]._init()
            # Create your alpha array and fill the colormap with them.
            alphas = np.linspace(0, 1, cmaps[i].N + 3)
            # Create the _lut array, with rgba values
            cmaps[i]._lut[:, -1] = alphas

        # Draw piano roll and stack image on a1
        for i in range(channel_nb):
            try:
                a1.imshow(roll[i], origin="lower", interpolation='nearest', cmap=cmaps[i], aspect='auto')
            except IndexError:
                pass

        # Draw color bar
        colors = [mpl.colors.hsv_to_rgb((i / channel_nb, 1, 1)) for i in range(channel_nb)]
        cmap = mpl.colors.LinearSegmentedColormap.from_list('my_cmap', colors, 16)
        # colour panel
        a2 = fig.add_axes([0, 0, 0, 0])  # Make the color bar axes invisible
        cbar = mpl.colorbar.ColorbarBase(a2, cmap=cmap,
                                         orientation='horizontal',
                                         ticks=list(range(16)))

        # Show piano roll
        plt.draw()
        plt.ion()
        # Save the piano roll as a .png file
        plt.savefig(filename, format='png')

    def __init__(self, filename):

        mido.MidiFile.__init__(self, filename)
        self.sr = 10
        self.meta = {}
        self.events = self.get_events()

    def get_events(self):
        mid = self
        print(mid)

        # There is > 16 channel in midi.tracks. However there is only 16 channel related to "music" events.
        # We store music events of 16 channel in the list "events" with form [[ch1],[ch2]....[ch16]]
        # Lyrics and meta data used a extra channel which is not include in "events"

        events = [[] for x in range(16)]

        # Iterate all event in the midi and extract to 16 channel form
        for track in mid.tracks:
            for msg in track:
                try:
                    channel = msg.channel
                    events[channel].append(msg)
                except AttributeError:
                    try:
                        if type(msg) != type(mido.UnknownMetaMessage):
                            self.meta[msg.type] = msg.dict()
                        else:
                            pass
                    except:
                        print("error", type(msg))

        return events

    def get_roll(self):
        events = self.get_events()
        sr = self.sr
        length = self.get_total_ticks()
        print("Total ticks:", length)  # Debugging
        roll = np.zeros((16, 128, length // sr + 1), dtype="int8")
        note_register = [int(-1) for x in range(128)]
        timbre_register = [1 for x in range(16)]

        for idx, channel in enumerate(events):
            time_counter = 0
            volume = 100

            for msg in channel:
                if msg.type == "control_change":
                    if msg.control == 7:
                        volume = msg.value
                    if msg.control == 11:
                        volume = volume * msg.value // 127

                if msg.type == "program_change":
                    timbre_register[idx] = msg.program

                if msg.type == "note_on":
                    note_on_start_time = time_counter // sr
                    note_on_end_time = (time_counter + msg.time) // sr
                    intensity = volume * msg.velocity // 127

                    if note_register[msg.note] == -1:
                        note_register[msg.note] = (note_on_end_time, intensity)
                    else:
                        old_end_time = note_register[msg.note][0]
                        old_intensity = note_register[msg.note][1]
                        roll[idx, msg.note, old_end_time: note_on_end_time] = old_intensity
                        note_register[msg.note] = (note_on_end_time, intensity)

                if msg.type == "note_off":
                    note_off_start_time = time_counter // sr
                    note_off_end_time = (time_counter + msg.time) // sr
                    note_on_end_time = note_register[msg.note][0]
                    intensity = note_register[msg.note][1]
                    roll[idx, msg.note, note_on_end_time:note_off_end_time] = intensity
                    note_register[msg.note] = -1

                time_counter += min(msg.time + 10, length - time_counter)

        return roll

    def get_roll_image(self):
        roll = self.get_roll()
        plt.ioff()

        K = 16

        transparent = colorConverter.to_rgba('black')
        colors = [mpl.colors.to_rgba(mpl.colors.hsv_to_rgb((i / K, 1, 1)), alpha=1) for i in range(K)]
        cmaps = [mpl.colors.LinearSegmentedColormap.from_list('my_cmap', [transparent, colors[i]], 128) for i in
                 range(K)]

        for i in range(K):
            cmaps[i]._init()  # create the _lut array, with rgba values
            # create your alpha array and fill the colormap with them.
            # here it is progressive, but you can create whathever you want
            alphas = np.linspace(0, 1, cmaps[i].N + 3)
            cmaps[i]._lut[:, -1] = alphas

        fig = plt.figure(figsize=(4, 3))
        a1 = fig.add_subplot(111)
        a1.axis("equal")
        a1.set_facecolor("black")


        array = []

        for i in range(K):
            try:
                img = a1.imshow(roll[i], interpolation='nearest', cmap=cmaps[i], aspect='auto')
                array.append(img.get_array())
            except IndexError:
                pass
        return array


    def get_tempo(self):
        try:
            return self.meta["set_tempo"]["tempo"]
        except:
            return 500000

    def get_total_ticks(self):
        max_ticks = 0
        for channel in range(16):
            ticks = sum(msg.time for msg in self.events[channel])
            if ticks > max_ticks:
                max_ticks = ticks
        return max_ticks
