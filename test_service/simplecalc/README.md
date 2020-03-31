This is a sample service written in C. Feel free to use it as starting point for your code :)

Run `make` to create a bundle you can sumbit.


Files
=====

  - `service/`: the service meat -- only these files get on the VM and are seen by players, put in everything that is needed!
  - `scripts/`: benign functionality for your service (flag setting / retrieval), and exploit samples.
  - `src/`: submit this as your source (note: this is just for organizers' reference).


Recommendations for C
=====================

Keep in mind that your service will run over the network, not on a terminal.

Long story short, put a `setbuf(stdin, NULL)` before using `printf()` :)

If you prefer `read()` / `write()`, see our `in()` and `out()` helpers in [utils.h](src/utils.h). If necessary, you can also use `shutdown()` and `setsockopt()` (see `man tcp`).
