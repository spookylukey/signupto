============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://bitbucket.org/spookylukey/signupto/issues.

If you are reporting a bug, please include:

* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix bugs and implement features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the BitBucket issues for bugs or features that you want to tackle.

Write Documentation
~~~~~~~~~~~~~~~~~~~

signupto could always use more documentation, whether as part of the
official signupto docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://bitbucket.org/spookylukey/signupto/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)



Get Started!
------------

Ready to contribute? Here's how to set up `signupto` for local development.

1. Fork the `signupto` repo on BitBucket.
2. Clone your fork locally::

    $ hg clone ssh://hg@bitbucket.org/your_name_here/signupto

3. Install your local copy into a virtualenv. Assuming you have
   virtualenvwrapper installed, this is how you set up your fork for local
   development::

    $ mkvirtualenv signupto
    $ cd signupto/
    $ python setup.py develop

4. Create a branch for local development::

    $ hg branch name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the tests, including testing other Python versions with tox::

    $ tox

   You will need to:

    $ pip install tox

6. Commit your changes and push your branch to BitBucket::

    $ hg record
    $ hg push

7. Submit a pull request through the BitBucket website.
