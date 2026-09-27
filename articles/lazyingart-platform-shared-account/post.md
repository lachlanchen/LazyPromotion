---
id: 3873
title: "A Home for the Tools, Without Another Login to Remember"
slug: "lazyingart-platform-tools-shared-account"
status: "publish"
source_language: "en"
categories:
  - "Computer & Internet"
excerpt: "Find LazyingArt's apps in one place, and a look at the shared account being built around EchoMind, Google, Apple and GitHub sign-in."
---

The tools started with different problems. L & N came from confusing two sounds. Bunko keeps reading help beside a page. AiMemo gives a thought somewhere to land before it disappears. They belong together, but finding them should not mean searching through a long list of repositories.

[LazyingArt Platform](https://platform.lazying.art/) is their front door. You can browse the apps, read how they work, watch a short demonstration and follow the official store link. There is no account wall around the catalogue.

The next piece is a shared LazyingArt account. It is being built around EchoMind’s account framework, with an existing EchoMind account and Google, Apple, GitHub or email as the intended ways to sign in. **Shared sign-in is not live on the platform yet.** Until it is, each app keeps its current login.

## One identity, separate places to work

The point is to stop making people start over every time they try another tool. The intended flow is a single LazyingArt sign-in page, followed by a return to the app you opened.

That should not turn every app into one shared folder. A memo belongs in your memo workspace; a paper and its private notes belong in your reading workspace. Signing in identifies you. It does not publish your notes, buy an app or connect a wallet.

EchoMind access also stays separate from a general LazyingArt account. A shared identity should not require an invitation just to use an unrelated tool, nor should it silently grant access to a service with its own membership rules.

## The small technical detail that matters

The framework uses a central account service, with a separate connection for each app. The app receives a limited sign-in result rather than your Google, Apple or GitHub password. An existing account needs a verified link; two matching email addresses alone are not enough to merge private workspaces.

The account code and app adapters are being tested, but the production shared-login routes remain disabled. The next milestone is a real sign-in and return through each supported provider, with cancellation and sign-out working too. A button on a page would not be enough.

## What you can use today

Browse [the platform](https://platform.lazying.art/), choose a tool and use its existing entry point. If you already use EchoMind, its [current sign-in page](https://chat.lazying.art/login) is available now. The platform’s Account section separates that working link from the shared sign-in that is coming next.

The aim is simple: spend less time finding the right app and getting back into it, and more time doing the thing you came for.
