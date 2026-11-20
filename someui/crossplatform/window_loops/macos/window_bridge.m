#import <Cocoa/Cocoa.h>
#include <stdlib.h>

#define WB_EXPORT __attribute__((visibility("default")))

#if defined(__cplusplus)
extern "C" {
#endif

typedef void (*WBEventCallback)(void *user_data);

@interface WBWindowObserver : NSObject
@property (nonatomic, assign) WBEventCallback onEvent;
@property (nonatomic, assign) void *userData;
@property (nonatomic, weak) NSWindow *observedWindow;
- (void)handleNotification:(NSNotification *)note;
@end

@implementation WBWindowObserver

- (void)handleNotification:(NSNotification *)note {
    if (self.onEvent) {
        self.onEvent(self.userData);
    }
}

- (void)dealloc {
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

@end

typedef struct WBLoop {
    __strong NSRunLoop *runLoop;
} WBLoop;

WB_EXPORT WBLoop *wb_loop_create(void) {
    WBLoop *ctx = (WBLoop *)calloc(1, sizeof(WBLoop));
    if (!ctx) {
        return NULL;
    }
    ctx->runLoop = [NSRunLoop currentRunLoop];
    return ctx;
}

WB_EXPORT void wb_loop_step(WBLoop *ctx, double timeout_sec) {
    if (!ctx || !ctx->runLoop) {
        return;
    }
    @autoreleasepool {
        double clamped = timeout_sec < 0.0 ? 0.0 : timeout_sec;
        NSDate *limitDate = [NSDate dateWithTimeIntervalSinceNow:clamped];
        [ctx->runLoop runMode:NSDefaultRunLoopMode beforeDate:limitDate];
    }
}

WB_EXPORT void wb_loop_wakeup(WBLoop *ctx) {
    if (!ctx || !ctx->runLoop) {
        return;
    }
    CFRunLoopRef cfLoop = [ctx->runLoop getCFRunLoop];
    if (cfLoop) {
        CFRunLoopWakeUp(cfLoop);
    }
}

WB_EXPORT void wb_loop_destroy(WBLoop *ctx) {
    if (!ctx) {
        return;
    }
    @autoreleasepool {
        ctx->runLoop = nil;
    }
    free(ctx);
}

WB_EXPORT void *wb_attach_window(void *nswindow_ptr, WBEventCallback cb, void *user_data) {
    if (!nswindow_ptr || !cb) {
        return NULL;
    }
    @autoreleasepool {
        NSWindow *win = (__bridge NSWindow *)nswindow_ptr;
        if (![win isKindOfClass:[NSWindow class]]) {
            return NULL;
        }

        WBWindowObserver *obs = [[WBWindowObserver alloc] init];
        obs.onEvent = cb;
        obs.userData = user_data;
        obs.observedWindow = win;

        NSNotificationCenter *nc = [NSNotificationCenter defaultCenter];
        [nc addObserver:obs
               selector:@selector(handleNotification:)
                   name:NSWindowDidResizeNotification
                 object:win];
        [nc addObserver:obs
               selector:@selector(handleNotification:)
                   name:NSWindowWillCloseNotification
                 object:win];

        return (__bridge_retained void *)obs;
    }
}

WB_EXPORT void wb_detach_window(void *observer_ptr) {
    if (!observer_ptr) {
        return;
    }
    @autoreleasepool {
        WBWindowObserver *obs = (__bridge_transfer WBWindowObserver *)observer_ptr;
        [[NSNotificationCenter defaultCenter] removeObserver:obs];
        obs.onEvent = NULL;
        obs.userData = NULL;
        obs.observedWindow = nil;
    }
}

#if defined(__cplusplus)
}
#endif