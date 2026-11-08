That background listing is finished, and it changes nothing in my report.

- **Leftovers:** the shared temporary folder holds no `p1-real-*` or `p1-twin-*` directory. It is 516 MB in all, and that includes other sessions' pytest folders.
- **Disclosure fix:** the sandbox size I gave was too high. I wrote "a few GB", and I did not measure it.
- **New CLAUDE.md item 10:** the re-read adds only a restatement of the dangling-junction note I already worked under. My tests made no junction.

**The verdict stands: NOT READY.**
- **D1:** git's output is decoded with the locale's code page. A modified checkout with a non-ASCII name under `core.quotePath=false` gives exit 3 and a traceback where exit 2 is due.
- **D2:** an ignored untracked file in the checkout is not seen, although the page says untracked files are seen whatever the checkout's settings say.

Both are in `check_moth`. The full report is my previous message.
