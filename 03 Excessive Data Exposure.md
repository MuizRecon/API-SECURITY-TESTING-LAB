# Excessive Data Exposure on the Video Details Endpoint (Leaking Internal Processing Parameters)

## Why I looked here

After testing the video upload functionality, I wanted to see exactly what information the application returned about uploaded videos. File upload features often expose more metadata than users actually need, especially when backend processing is involved.

My expectation was simple: once a video is uploaded, the API should only return information that's useful for displaying it back to the user, such as its name, thumbnail, or identifier. Anything related to how the server internally processes that file would be unnecessary in a user-facing response.

## Finding the unnecessary data exposure

After uploading a video through the profile page, I captured the request used to retrieve its details:

```http
GET /identity/api/v2/user/videos/52
Authorization: Bearer <eyJhbGci0iJSUzI1NiJ9.eyJzdWIi *****UnERQ8**********************Q8zWlLOV_dPNGzlFhA6KYNkchwIvbaJavsEKOdQlJwKjHQRV1GxX9-WrzZ-tbYNhhYJl6pxlwROphi9KRRw
```

The response initially looked perfectly normal:

```json
{
  "id": 52,
  "video_name": "sample-5s.mp4",
  "conversion_params": "-v codec h264",
  "profileVideo": "data:image/jpeg;base64,..."
}
```
[Burp Suite Request and Response](../main/screenshots/Excessive-Data-Exposure.png)
Most of the fields made sense for a client application. The video ID identifies the resource, the filename is displayed to the user, and the thumbnail is used by the frontend.

One field immediately stood out though:

```json
"conversion_params": "-v codec h264"
```

Unlike the other properties, this isn't user data. It's an internal processing parameter describing how the backend converts uploaded videos before storing or serving them.

A client has no legitimate reason to know the command or parameters used by the server's video processing pipeline.

## Confirming the exposure

To verify this wasn't an isolated response, I retrieved the details of multiple uploaded videos using the same endpoint.

Each response consistently included the `conversion_params` field, regardless of which video was requested.

This indicates the application intentionally exposes this internal property as part of the API response instead of filtering it before sending data back to clients.

## Why this matters

This is an **Excessive Data Exposure** issue that maps to **Broken Object Property Level Authorization**. While the endpoint correctly restricts access to the user's own videos, it exposes internal implementation details that should remain server-side.

The exposed field reveals part of the application's media processing pipeline:

* the backend performs video conversion after upload
* the conversion uses H.264 encoding parameters
* internal processing configuration is directly exposed to API consumers

On its own, this information is unlikely to result in immediate compromise. However, unnecessary disclosure of backend implementation details reduces the attacker's uncertainty and can help during reconnaissance.

If additional weaknesses existed within the media processing pipeline, knowing the exact conversion parameters could make it easier to craft malicious media files or target the underlying conversion service.

## Root cause

The endpoint returns the complete backend object rather than only the properties required by the frontend.

Instead of exposing a minimal response model, it includes internal implementation fields that should never leave the server.

## How I'd fix it

The API should return only properties that are necessary for the client application.

For example:

```json
{
  "id": 52,
  "video_name": "sample-5s.mp4",
  "profileVideo": "data:image/jpeg;base64,..."
}
```

Internal processing parameters such as `conversion_params` should remain exclusively within the backend and never be serialized into API responses.

More broadly, API responses should use dedicated response models or DTOs rather than exposing database entities directly. This helps ensure only intended fields are returned to clients.

## Where this fits

This maps to **OWASP API3:2023 – Broken Object Property Level Authorization (Excessive Data Exposure)**.

---

**Lesson I'm taking forward:** not every useful finding comes from bypassing authentication or authorization. Sometimes simply comparing what the frontend actually needs against what the API returns is enough to uncover unnecessary information disclosure. Whenever I encounter API responses that include implementation details, configuration values, internal flags, or processing metadata, they're worth questioning because they often reveal far more about the application's architecture than intended.
