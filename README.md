# Cached image optimizer

This library fetches images via HTTP(S), optimizes them and stores into some storages.

## Usage

The standard way to use this library is store metadata in Redis and store images itself in S3. The images in S3 can be accessed by the internet.

You have to implement your own Redis and S3 handler which extends `StorageBase`
