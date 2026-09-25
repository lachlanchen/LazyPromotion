# Product video library

Checked September 26, 2026. Channel: [The Art of Lazying — @lazyingart](https://www.youtube.com/@lazyingart). This is a reusable public-media index, not a posting queue.

## App walkthroughs

| Product | Recording | Review and use |
| --- | --- | --- |
| L & N | [English walkthrough](https://www.youtube.com/shorts/Nlsx_5U6g6U) | Native player opened; correct channel, app and English captions checked. Used in the [r/SideProject introduction](https://www.reddit.com/r/SideProject/comments/1wpvosw/l_n_i_mix_up_l_and_n_so_i_built_a_pronunciation/). |
| Bunko | [Bunko App: Read World Classics with Ruby Annotations](https://www.youtube.com/shorts/pSWnOwzyc-4) | Native player opened; Bunko and multilingual burned-in captions including English checked. The recording shows a TestFlight-installed version, so check displayed features against the current public release before making store claims. |

Both are existing creator recordings, not generated concept videos or customer testimonials. The visual check is not a full editorial/audio audit. Do not re-upload them merely to share a link. The older `jirylmFo5U8` link identifies a Local Knowledge Terminal video, not L & N.

### Store path added September 26

The two English demo descriptions lacked direct store destinations. YouTube's
[link guidance](https://support.google.com/youtube/answer/13748639?hl=en) says
Shorts description/comment URLs are not clickable, but channel-profile links are.
The existing uploads were retained, and the channel now has three profile links:

- **L & N — App Store**: <https://apps.apple.com/us/app/l-n-speech-practice/id6808872450>
- **L & N — Google Play**: <https://play.google.com/store/apps/details?id=art.lazying.landn>
- **Bunko — App Store**: <https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919>

There were no existing channel-profile links to replace. The channel name,
handle, description, translations, contact field and branding were left alone.
All three labels and destinations were checked on the public channel page after
the saved settings survived a reload; the store IDs also appear in an anonymous
channel-page response. YouTube's redirect tokens are not stored in public records.

The L & N video description now begins:

> Get L & N: Speech Practice through the App Store and Google Play links on my channel profile. iPhone/iPad: US$0.99. Android: free download with in-app purchases.

The Bunko video description now begins:

> Bunko: Classics with Ruby is US$0.99 once on iPhone/iPad. The "Bunko — App Store" link is on my channel profile.

Only those prefixes were added. Original description bodies, including Bunko's
free reader link, were preserved. Titles, uploaded media, visibility and playlists
were not changed. Both saves were verified after reload and then matched exactly
against anonymous public video metadata at 17:36 UTC on September 25 (September
26 in Hong Kong).

| Existing video | Full updated description SHA-256 |
| --- | --- |
| `Nlsx_5U6g6U` | `02275aba861564b6aa80d82f9504da7e07c65d09e749f7a3a0e805e35673418f` |
| `pSWnOwzyc-4` | `7dede50d4484ddd349cd2a0fc015b77beca42cb92db83a809fd14ba09109858b` |

Hashes use UTF-8 text with outer whitespace removed. They record this historical
update, not permission to overwrite future edits. This improves the route from
an existing demonstration to a store; no click, install or sale is inferred.

## Editing and publishing — material to review

The channel search surfaced these potentially relevant recordings. Titles and channel placement were checked; their full contents and current software relevance have **not** yet been reviewed for a new promotion.

- [Automated Video Publishing System – Multi-Platform & Multi-Language](https://www.youtube.com/watch?v=5sfJwp-sgrQ).
- [Unlocking the Secrets of Instant Content Creation](https://www.youtube.com/watch?v=eowNGsPDzQs).
- [Fixing Subtitles: A Journey Through Voice Detection and Bugs](https://www.youtube.com/watch?v=AlifKqFxjW0).
- [Boosting Your Subtitle Game: Precision in Video Transcripts!](https://www.youtube.com/watch?v=ZkLbwHw2zG8).

### Separate builder story

The strongest concrete angle is **from one recorded product demo to corrected multilingual subtitles and a reviewed publishing handoff**. Show a source clip, its corrected captions and the finished app walkthrough, then explain which part of the workflow each repository owns:

- [LazyEdit](https://github.com/lachlanchen/LazyEdit): transcription, subtitle correction/translation, burn-in and metadata preparation.
- [AutoPubMonitor](https://github.com/lachlanchen/AutoPubMonitor): monitoring and synchronization for the publication workflow.
- [AutoPublish](https://github.com/lachlanchen/AutoPublish): publishing through platform-specific workflows.
- [AutoPublication](https://github.com/lachlanchen/AutoPublication): the umbrella project; verify current structure before using it as an installation entry point.

Lead with the repeated editing/publishing problem and an actual demonstrated workflow, not a promise of passive income or unattended publishing to every platform. Recheck setup requirements and platform support, and review the selected recording before composing a separate introduction. No LazyEdit or AutoPublish social post was published or scheduled in this session.
