from datetime import datetime, date, timedelta
import dateutil.parser as date_parser
import enum
from turtle import st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
import math
import re
import json
import time


class Media:
    def __init__(self, date, speaker):
        self.date = date
        self.day = date.date()
        self.time = date.time()
        self.speaker = speaker


class Message(Media):
    def __init__(self, date, speaker, text):
        self.date = date
        self.day = date.date()
        self.time = date.time()
        self.speaker = speaker
        self.text = text

        self._get_words()

    def _get_words(self):
        self.words = re.findall("\w+'\w+|\w+", self.text)
        self.words_lower = [word.lower() for word in self.words]

    def count_regex(self, regex, case_sensitive=False):
        if case_sensitive:
            return len(re.findall(regex, self.text))

        else:
            return len(re.findall(regex, self.text, re.IGNORECASE))


class Messages():
    def __init__(self):
        self.messages = []
        self.speakers = []

    def sort(self):
        self.messages.sort(key=lambda s: s.date)

        self.speakers.sort()


class Column():
    def __init__(self, word=None, case=None, speaker=None, norm=None, average=None):
        self.word = word
        self.case = case
        self.speaker = speaker
        self.norm = norm
        self.average = average

    def get(self, depth=5):
        raw_column = (self.word, self.case, self.speaker,
                      self.norm, self.average)

        column = ()

        for i in raw_column[:depth]:
            if i != None:
                column += (i,)

        return column

    def get_name(self):
        name = ""

        if self.word == "Num words" or self.word == "Num messages":
            name += self.word + ", "

        else:
            if self.case == "Case insensitive":
                name += '"' + self.word + '", case insens., '

            else:
                name += '"' + self.case + '", case sens., '

        if self.speaker != "All":
            name += self.speaker + " only, "

        if self.norm != "None":
            name += "norm. by \"" + self.norm + "\", "

        if self.average != 1:
            name += str(self.average) + "-day average, "

        return name[:-2]


class SelectionDropdown():
    def __init__(self, frame, text, options, var_type, default_value):
        tk.Label(frame, text=text).pack(side=tk.LEFT)

        if var_type == "str":
            self.var = tk.StringVar()
        elif var_type == "int":
            self.var = tk.IntVar()

        self.var.set(default_value)

        self.dropdown = tk.OptionMenu(
            frame,
            self.var,
            *options,
            command=selection_ui.update_dropdowns)
        self.dropdown.pack(side=tk.LEFT)

    def set_new_options(self, new_values):
        def lambda_command(value):
            self.var.set(value)
            selection_ui.update_dropdowns()

        menu = self.dropdown["menu"]
        menu.delete(0, "end")

        for value in new_values:
            menu.add_command(label=value,
                             command=lambda value=value: lambda_command(value))

        if not self.var.get() in new_values:
            self.var.set(new_values[0])


class Selection():
    def __init__(self, parent_frame, include_adds=True, preset=Column("Num words", "N/A", "All", "None", 1)):
        self.frame = tk.Frame(parent_frame)
        self.frame.pack()

        self.word = SelectionDropdown(
            self.frame,
            "Word:",
            get_headings(data),
            "str",
            preset.word
        )

        self.case = SelectionDropdown(
            self.frame,
            "Case:",
            get_headings(data[self.word.var.get()]),
            "str",
            preset.case
        )

        self.speaker = SelectionDropdown(
            self.frame,
            "Speaker:",
            get_headings(data
                         [self.word.var.get()]
                         [self.case.var.get()]),
            "str",
            preset.speaker
        )

        self.norm = SelectionDropdown(
            self.frame,
            "Normalised:",
            get_headings(data
                         [self.word.var.get()]
                         [self.case.var.get()]
                         [self.speaker.var.get()]),
            "str",
            preset.norm
        )

        if include_adds:
            tk.Button(self.frame, text="Add normalisation",
                      command=self.add_norm).pack(side=tk.LEFT)

        self.average = SelectionDropdown(
            self.frame,
            "x-day average:",
            get_headings(data
                         [self.word.var.get()]
                         [self.case.var.get()]
                         [self.speaker.var.get()]
                         [self.norm.var.get()]),
            "int",
            preset.average
        )

        if include_adds:
            tk.Button(self.frame, text="Add x-day average",
                      command=self.add_x_day_average).pack(side=tk.LEFT)

            tk.Button(self.frame, text="Delete",
                      command=self.delete).pack(side=tk.LEFT)

        self.deleted = False

    def update_dropdowns(self, data):
        if not self.deleted:
            self.word.set_new_options(
                get_headings(data)
            )
            self.case.set_new_options(
                get_headings(data
                             [self.word.var.get()])
            )
            self.speaker.set_new_options(
                get_headings(data
                             [self.word.var.get()]
                             [self.case.var.get()])
            )
            self.norm.set_new_options(
                get_headings(data
                             [self.word.var.get()]
                             [self.case.var.get()]
                             [self.speaker.var.get()])
            )
            self.average.set_new_options(
                get_headings(data
                             [self.word.var.get()]
                             [self.case.var.get()]
                             [self.speaker.var.get()]
                             [self.norm.var.get()])
            )

    def get_column(self):
        if not self.deleted:
            return Column(
                self.word.var.get(),
                self.case.var.get(),
                self.speaker.var.get(),
                self.norm.var.get(),
                self.average.var.get(),
            )

    def add_x_day_average(self, *args, **kwargs):
        popup = EntryPopup(main_window.root)

        main_window.root.wait_window(popup.top)

        try:
            x_day_average(data, self.get_column(), int(popup.value))

            selection_ui.update_dropdowns()

            self.average.var.set(int(popup.value))

            graph_ui.redraw_graphs()

        except ValueError:
            pass

    def add_norm(self, *args, **kwargs):
        popup = ColumnPopup(main_window.root, self.get_column())

        main_window.root.wait_window(popup.top)

        if popup.column.word != None:
            normalise_column(data, self.get_column(),
                             normalise_by=popup.column)

            self.norm.var.set(popup.column.get_name())

            selection_ui.update_dropdowns()

            self.norm.var.set(popup.column.get_name())

            graph_ui.redraw_graphs()

    def delete(self):
        self.frame.destroy()

        self.deleted = True

        graph_ui.redraw_graphs()


class MainWindow():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(file_name)
        self.root.geometry("1200x900")


class SearchUI():
    def __init__(self, master):
        self.master = master

        self.frame = tk.LabelFrame(
            master, relief=tk.GROOVE, border=2, padx=5, pady=5, text="Search")
        self.frame.pack(fill=tk.X, padx=5, pady=(5, 2.5))
        self.frame.grid_columnconfigure(1, weight=1)

        tk.Label(self.frame, text="Search (entire) word: ").grid(column=0,
                                                                 row=0, sticky="e")
        self.entry = tk.Entry(self.frame)
        self.entry.grid(column=1, row=0, sticky="we")
        self.entry.bind("<Return>", self._on_click_search)

        # tk.Label(self.frame, text="Whole word: ").grid(
        #     column=0, row=1, sticky="e")
        self.whole_word_var = tk.BooleanVar()
        self.whole_word_var.set(True)
        self.whole_word_check = tk.Checkbutton(
            self.frame, variable=self.whole_word_var, command=self._update_UI)
        # self.whole_word_check.grid(column=1, row=1, sticky="w")

        tk.Label(self.frame, text="Use regex search: ").grid(
            column=0, row=2, sticky="e")
        self.regex_var = tk.BooleanVar()
        self.regex_check = tk.Checkbutton(
            self.frame, variable=self.regex_var, command=self._update_UI)
        self.regex_check.grid(column=1, row=2, sticky="w")

        tk.Label(self.frame, text="Regex: ").grid(column=0, row=3, sticky="e")
        self.regex_entry = tk.Entry(self.frame, state=tk.DISABLED)
        self.regex_entry.insert(0, "\w+'\w+|\w+")
        self.regex_entry.grid(column=1, row=3, sticky="we")
        self.regex_entry.bind("<Return>", self._on_click_search)

        self.readout = tk.Label(self.frame, text=" ")
        self.readout.grid(column=0, row=5, columnspan=3, sticky="ew")

        self.bar = ttk.Progressbar(
            self.frame, orient=tk.HORIZONTAL, length=200, mode="determinate")
        self.bar.grid(column=0, row=4, columnspan=3, sticky="ew", pady=(5, 0))

        tk.Button(self.frame, text="Search", command=self._on_click_search).grid(
            column=2, row=0, rowspan=4, sticky="ns", padx=(5, 0))

    def set_progress_bar(self, value):
        self.bar['value'] = value * 100
        self.master.update()

    def set_task_readout(self, text):
        self.readout.config(text=text)
        self.master.update()

    def _on_click_search(self, *args, **kwargs):
        ok = True

        if self.regex_var.get():
            if self.regex_entry.get() == "":
                ok = False

        else:
            if self.entry.get() == "":
                ok = False

        if ok:
            number_word_per_day_tk()

    def _update_UI(self, *args, **kwargs):
        '''if self.whole_word_var.get():
            self.regex_var.set(False)
            self.regex_check.config(state=tk.DISABLED)
        else:
            self.regex_check.config(state=tk.NORMAL)'''

        if self.regex_var.get():
            self.regex_entry.config(state=tk.NORMAL)
            self.entry.config(state=tk.DISABLED)
            self.whole_word_check.config(state=tk.DISABLED)

        else:
            self.regex_entry.config(state=tk.DISABLED)
            self.entry.config(state=tk.NORMAL)
            self.whole_word_check.config(state=tk.NORMAL)

    def get_regex(self):
        if self.regex_var.get():
            return self.regex_entry.get()

        elif self.whole_word_var.get():
            return "(\W+|^)" + self.entry.get() + "(\W|$)"

        else:
            return self.entry.get()

    def get_column(self, case_sensitive=False):
        if self.regex_var.get():
            return Column("Regex: " + self.get_regex(), "N/A")

        else:
            case = (self.entry.get() if case_sensitive else "Case insensitive")

            return Column(self.entry.get().lower(), case)


class SelectionUI():
    def __init__(self, master):
        self.frame = tk.LabelFrame(
            master, relief=tk.GROOVE, border=2, padx=5, pady=5, text="Choose what to plot")
        self.frame.pack(fill=tk.X, padx=5, pady=2.5)

        self.selections = []

        self.selections_frame = tk.Frame(self.frame)
        self.selections_frame.pack()

        tk.Button(self.frame, text="Add graph",
                  command=self.add_graph).pack(fill=tk.X)

    def add_graph(self, preset=Column("Num words", "N/A", "All", "None", 5), *args, **kwargs):
        self.selections.append(Selection(self.selections_frame, preset=preset))

        graph_ui.redraw_graphs()

    def update_dropdowns(self, *args, **kwargs):
        for selection in self.selections:
            selection.update_dropdowns(data)

        graph_ui.redraw_graphs()


class GraphUI():
    def __init__(self, master):
        self.frame = tk.LabelFrame(master, relief=tk.GROOVE,
                                   border=2, padx=5, pady=5, text="Graph")
        self.frame.pack(fill=tk.BOTH, expand=1, padx=5, pady=(2.5, 5))

        self.fig = Figure()
        self.plot = self.fig.add_subplot(111)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH)

    def plot_data(self, data, columns):
        self.plot.clear()

        self.plot.plot(data.loc[:, [column.get() for column in columns]])
        self.plot.set_ylim((0, None))
        self.plot.set_xlim((data.index[0], data.index[-1]))
        self.plot.legend([column.get_name() for column in columns])

        plt.show()

        self.canvas.draw()

    def redraw_graphs(self):
        columns = []

        for i in selection_ui.selections:
            if not i.deleted:
                columns.append(i.get_column())

        self.plot_data(data, columns)


class EntryPopup():
    def __init__(self, master):
        self.top = tk.Toplevel(master)

        self.label = tk.Label(self.top, text="Enter a number:")
        self.label.pack()

        self.entry = tk.Entry(self.top)
        self.entry.bind("<Return>", self.cleanup)
        self.entry.pack()
        self.entry.focus()

        self.button = tk.Button(self.top, text='Ok', command=self.cleanup)
        self.button.pack()

        self.value = ""

    def cleanup(self, *args, **kwargs):
        self.value = self.entry.get()
        self.top.destroy()


class ColumnPopup():
    def __init__(self, master, current_column):
        self.top = tk.Toplevel(master)

        self.label = tk.Label(
            self.top, text="Choose a column to normalise by:")
        self.label.pack()

        self.selection = Selection(self.top, include_adds=False, preset=Column(
            "Num words", "N/A", current_column.speaker, "None", 1))

        self.button = tk.Button(self.top, text='Ok', command=self.cleanup)
        self.button.pack(fill=tk.X)

        self.column = Column()

    def cleanup(self, *args, **kwargs):
        self.column = self.selection.get_column()
        self.top.destroy()


# TODO messages over time of day/year
# TODO file select
# TODO only search column if necessary


def create_days_dict(messages):
    first_day = messages.messages[0].day
    last_day = messages.messages[-1].day

    keys = []

    day_counter = first_day

    while day_counter <= last_day:
        keys.append(day_counter)

        day_counter += timedelta(days=1)

    return dict((key, 0) for key in keys)


def parse_file(file_name, include_media=False, file_type=None):
    raw = open(file_name, "r", encoding="utf8").read()

    if file_type == None:
        if file_name[-5:] == ".json":
            file_type = "facebook"

        elif raw[0][0] == "[":
            file_type = "iphone"

        else:
            file_type = "whatsapp"

    print("Detected file type: " + file_type)

    iphone = False
    if raw[0][0] == "[":
        iphone = True

    messages = Messages()

    if file_type == "facebook":
        jraw = json.loads(raw)

        messages.speakers = [i["name"] for i in jraw["participants"]]

        for message in jraw["messages"]:
            if "content" in message.keys():
                date = datetime.fromtimestamp(message["timestamp_ms"]/1000)
                name = message["sender_name"]
                text = message["content"]

                messages.messages.append(Message(date, name, text))

    elif file_type == "imessage":
        first_message = True

        date = ""
        name = ""
        text = ""

        for line in raw.split("\n"):
            line = line.strip()

            if line != "This message responded to an earlier message.":
                try:
                    new_date = date_parser.parse(line)
                    is_date = True

                    # Write old message to database
                    if not first_message:
                        text.strip("\n")

                        messages.messages.append(Message(date, name, text))

                        if not name in messages.speakers:
                            messages.speakers.append(name)

                        text = ""

                    line_type = "date"
                    date = new_date
                
                except date_parser._parser.ParserError:
                    is_date = False

                    if line_type == "date":
                        line_type = "name"
                        name = line
                        first_message = False

                    elif line_type == "name":
                        line_type = "text"
                        text += line

    else:
        for line in raw.split("\n")[1:]:
            # print("\t" + line.strip("\n"))

            try:
                # Handle multiline messages
                if (not(iphone) and line[17:20] == " - ") or (iphone and line[0] == "[" and line[11:13] == ", "):
                    if iphone:  # Handle iPhone exports seperately from android
                        [day, month, year] = line[1:11].split("/")
                        [hour, minute, second] = line[13:21].split(":")
                        name = line[23:].split(": ")[0]
                        text = line.split(name + ": ")[1].strip("\n")

                    else:  # Android
                        [day, month, year] = line.split(",")[0].split("/")
                        [hour, minute] = line.split(" ")[1].split(":")
                        second = 0
                        name = line.split(" - ")[1].split(":")[0]
                        text = line.split(name + ": ")[1].strip("\n")

                    date = datetime(int(year), int(month), int(
                        day), int(hour), int(minute), int(second))

                    if text == "<Media omitted>":
                        if include_media:
                            messages.messages.append(Media(date, name))

                    else:
                        messages.messages.append(Message(date, name, text))

                        if not name in messages.speakers:
                            messages.speakers.append(name)

                else:
                    messages.messages[-1].text += "\n" + line.strip("\n")

            except Exception:
                pass
                # print("Oh dear, I can't handle this line:")
                # print(line)


    messages.sort()

    return messages


def contains_column(data, column):
    columns = list(data.columns)
    column = column.get()

    for i in columns:
        if column == i[0:len(column)]:
            return True

    return False


def get_headings(data):
    return list(dict.fromkeys(data.columns.get_level_values(0)))


def format_speakers(speakers):
    speakers = sorted(speakers)

    if speakers == messages.speakers:
        return "All"

    else:
        name = ""

        for speaker in speakers:
            name += speaker + ", "

        return name[:-2]


def normalise_column(data, column, normalise_by=Column("Num words", "N/A", "All", "None", 1)):
    data[column.word, column.case, column.speaker, normalise_by.get_name(), 1] = \
        np.where(data[normalise_by.get()] == 0, 0,
                 data[column.get(depth=3) + ("None", 1)] / data[normalise_by.get()])

    return data


def x_day_average(data, column, x):
    values = [0] * len(data.index.tolist())

    lower_reach = math.floor(x/2)
    higher_reach = math.ceil(x/2) - 1

    column_num = data.columns.get_loc(column.get(depth=4) + (1,))

    for i in range(lower_reach, len(values) - higher_reach):
        values[i] = float(data.iloc[i-lower_reach:i +
                                    higher_reach + 1, column_num:column_num+1].sum() / x)

    data[column.get(depth=4) + (x,)] = values

    return data


def number_messages_per_day(data, messages, speakers=[]):
    if speakers == []:
        speakers = messages.speakers

    formatted_speakers = format_speakers(speakers)

    messages_per_day = dict((key, 0) for key in data.index.tolist())
    words_per_day = dict((key, 0) for key in data.index.tolist())

    for i in messages.messages:
        if i.speaker in speakers:
            messages_per_day[i.day] += 1
            words_per_day[i.day] += len(i.words)

    data["Num messages", "N/A", formatted_speakers,
         "None", 1] = messages_per_day.values()
    data["Num words", "N/A", formatted_speakers,
         "None", 1] = words_per_day.values()

    return data


def initial_num_searches(data, messages):
    # All speakers
    data = number_messages_per_day(data, messages, [])

    # Individual speakers
    for speaker in messages.speakers:
        data = number_messages_per_day(data, messages, [speaker])

    return data


def _number_word_per_day(data, messages, regex, speakers=[], case_sensitive=False, normalise=True):
    if speakers == []:
        speakers = messages.speakers

    formatted_speakers = format_speakers(speakers)

    col = search_ui.get_column(case_sensitive).get()
    column = Column(col[0], col[1], formatted_speakers, "None", 1)

    if not contains_column(data, column):
        words_per_day = dict((key, 0) for key in data.index.tolist())

        num_messages = len(messages.messages)

        search_ui.set_task_readout(
            "Working on: \"" + col[0] + "\", " + col[1] + ", " + formatted_speakers)

        for ind, i in enumerate(messages.messages):
            if i.speaker in speakers:
                words_per_day[i.day] += i.count_regex(regex, case_sensitive)

            if ind % 2000 == 0:
                search_ui.set_progress_bar((ind+1) / num_messages)

        search_ui.set_progress_bar(1)
        search_ui.set_task_readout("Done!")

        data[col[0], col[1], formatted_speakers,
             "None", 1] = words_per_day.values()

        if normalise:
            data = normalise_column(
                data, Column(col[0], col[1], formatted_speakers))

    else:
        print("Didn't compute " + str(column.get()) + " - column already exists")

    return data


def number_word_per_day(data, messages, regex, case_sensitive=False):
    # All speakers
    data = _number_word_per_day(
        data, messages, regex, speakers=[], case_sensitive=case_sensitive)

    # Individual speakers
    for speaker in messages.speakers:
        data = _number_word_per_day(data, messages, regex, speakers=[
                                    speaker], case_sensitive=case_sensitive)

    return data


def number_word_per_day_tk(*args, **kwargs):
    word = search_ui.entry.get()

    regex = search_ui.get_regex()

    search_word_per_day(data, messages, regex)

    selection_ui.update_dropdowns()

    # print(data)


def search_word_per_day(data, messages, regex):
    # if not (word.lower(), "Case insensitive") in data:
    number_word_per_day(data, messages, regex,
                        case_sensitive=False)

    if not search_ui.regex_var.get():
        number_word_per_day(data, messages, regex,
                            case_sensitive=True)

    return data


file_name = "jack.txt"
file_name = "chats\\katie-w\\" + file_name

messages = parse_file(file_name, file_type="imessage")

column_name_tuples = [("Num messages", "N/A", "All", "None", 1),
                      ("Num words", "N/A", "All", "None", 1)]
column_structure = pd.MultiIndex.from_tuples(
    column_name_tuples, names=[
        "word",
        "case",
        "speaker",
        "normalised",
        "x-day average"
    ]
)

data = pd.DataFrame(
    # pd.date_range(start=messages[0].day, end=messages[-1].day, freq="D")
    index=create_days_dict(messages),
    columns=column_structure
)

data = initial_num_searches(data, messages)


# root
main_window = MainWindow()

# search section
search_ui = SearchUI(main_window.root)

# graph plotting section
selection_ui = SelectionUI(main_window.root)

# matplotlib integration
graph_ui = GraphUI(main_window.root)


# initial searches
# data = search_word_per_day(data, messages, "Lol")
# data = search_word_per_day(data, messages, "lol")
# data = search_word_per_day(data, messages, "poo")

data = x_day_average(
    data, Column("Num words", "N/A", "All", "None"), 5)
data = x_day_average(
    data, Column("Num words", "N/A", messages.speakers[0], "None"), 5)
data = x_day_average(
    data, Column("Num words", "N/A", messages.speakers[1], "None"), 5)


# print(data)


selection_ui.add_graph(preset=Column(
    "Num words", "N/A", messages.speakers[0], "None", 5))
selection_ui.add_graph(preset=Column(
    "Num words", "N/A", messages.speakers[1], "None", 5))

main_window.root.mainloop()
