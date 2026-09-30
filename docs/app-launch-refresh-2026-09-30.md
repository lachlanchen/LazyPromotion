# App release and promotion refresh · September 30

This pass checked the latest repository work, improved live acquisition pages,
updated existing articles and distributed specific app workflows. Publication
is not a customer or a payment.

## What actually shipped

| App | Public destination | Still separate from the public release |
| --- | --- | --- |
| L & N | [Apple 1.0.9, US$0.99](https://apps.apple.com/us/app/l-n-speech-practice/id6808872450); [Google Play, free download with IAP](https://play.google.com/store/apps/details?id=art.lazying.landn) | Native Mac and the separate Android Pro package remain in review |
| Bunko | [iPhone/iPad/Watch 1.0.8](https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919); [native Mac 1.0.8](https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919?platform=mac), US$0.99 | Google public listing returns 404; 1.0.9 candidates are TestFlight builds |
| OnlyIdeas | [Native Mac 1.0.2, free](https://apps.apple.com/us/app/onlyideas/id6816392935?platform=mac), Intel and Apple silicon | iOS and Android remain in review; general paid plans are not activated |

The account inventory contained 163 repositories, 132 public; 214 sibling Git
workspaces were checked by latest commit. This is a freshness inventory, not a
deep audit of every codebase. No private repository name or credential is
published. Other recent store work includes submissions, not necessarily
public releases; pending apps do not get invented download buttons.

## Live owned pages

- [Main site](https://lazying.art/) and [43-entry directory](https://lazying.art/products/):
  OnlyIdeas becomes a featured Mac download, Bunko gets an explicit Mac route,
  and homepage metadata/localized copy reflect the new app. Commit `76bba5a`;
  48 tests passed; public HTML matches the committed files.
- [Product hub](https://platform.lazying.art/): OnlyIdeas Mac card, Bunko's
  explicit Watch-excerpt workflow and L & N saved-take practice. Commit
  `45adf3c`; 12 tests passed; public HTML/CSS match. Account service, credentials,
  ingress and NAT configuration stayed unchanged.
- [OnlyIdeas reading guide](https://blog.lazying.art/html/computer_internet/3864/onlyideas-read-papers-equations-questions.html):
  original/translation comparison, direct free Mac link and corrected import
  privacy wording. New imports default Shared; choose Only me for private work.
- [Bunko guide](https://blog.lazying.art/html/books/3853/bunko-chinese-japanese-classics-pinyin-furigana.html):
  Mac reading and explicitly transferred Watch excerpts, with both store links.

Both existing blog posts passed source/metadata guards, dry runs, exact
stored-body and public-link checks. Original publication metadata is preserved.
No new translation, customer account or payment object was created.
BLOG archive commit `81298e3` is pushed; unrelated working edits were preserved.

## Distribution

- [OnlyIdeas on X](https://x.com/lazyingart/status/2105091777585938559) is live.
  The native profile shows the complete text and original Mac App Store link.
- The [Bunko Watch demonstration](https://www.instagram.com/p/Dd5EmfqGZAA/) was
  delivered through Postiz at September 30, 00:42 UTC. Its native caption and
  account are verified. It uses the actual shipping Watch screenshot, not a
  concept image, and directs readers to the paid app.
- [OnlyIdeas on r/SideProject](https://www.reddit.com/r/SideProject/comments/1wtr5gy/)
  was submitted through Postiz at September 30, 00:44 UTC, but its native page
  says **removed by Reddit's filters**. This is not a qualified public placement,
  despite Postiz's PUBLISHED label. Community scope, posting restrictions and
  an exact-author duplicate search were checked before delivery. Do not repost,
  switch accounts or send an automated appeal.
- The [L & N recording-comparison post](../campaigns/l-and-n-saved-take-practice.json)
  is scheduled natively on X for October 1, 02:00 UTC. Both store links survived
  the native scheduled-list readback.
- OnlyIdeas' existing [Medium story](https://lazyingart.medium.com/d5026bc21dda)
  was updated in place and remains scheduled for September 30, 02:00 UTC,
  free to read with the owned blog canonical. No duplicate import.

Postiz removed URLs from the two X drafts even with regular-post settings.
Those two newly created, unpublished drafts were removed after their exact
IDs and DRAFT states were checked; copies remain in the private evidence.
Older held drafts were not touched. Native X was used once for
each intended item; Instagram and Reddit remain Postiz-managed. LinkedIn's
existing account hold is unchanged. No unsolicited replies or private messages
were sent, and no automated engagement loop was enabled.

## Follow-through

The older [Bunko Mac announcement](https://x.com/lazyingart/status/2104390638531957108)
and [book-community post](https://www.reddit.com/r/Recommend_A_Book/comments/1wscr1k/)
were verified live rather than reposted. The book post showed 275 views and no
reader comments. Views are not installations or sales.

The two Postiz items have completed delivery checks. Verify the remaining
Medium and native-X queues after their due times; review genuine questions
without a second pitch. Keep income null until qualified payment evidence
exists. The first verified USD1,000 goal remains active and unachieved.

Nineteen focused campaign tests pass. The full 1,095-test suite found three
pre-existing failures, reproduced on the untouched `ea71166` baseline: the
bundled native preview snapshot, an obsolete L & N article-destination assertion,
and a stale expected campaign version. They were recorded, not hidden or changed
to make this promotion pass appear fully green.
