import * as Haptics from 'expo-haptics';

export class HapticService {
  // Light haptic feedback for general interactions
  static light(): void {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  }

  // Medium haptic feedback for place recommendations
  static medium(): void {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
  }

  // Heavy haptic feedback for important notifications
  static heavy(): void {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
  }

  // Success notification
  static success(): void {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }

  // Warning notification
  static warning(): void {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
  }

  // Error notification
  static error(): void {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
  }

  // Custom pattern for place recommendations
  static placeRecommendation(): void {
    // Create a custom pattern: light tap, pause, medium tap
    setTimeout(() => {
      this.light();
      setTimeout(() => {
        this.medium();
      }, 200);
    }, 0);
  }

  // Selection feedback
  static selection(): void {
    Haptics.selectionAsync();
  }

  // Custom pattern for voice command recognition
  static voiceRecognition(): void {
    this.light();
    setTimeout(() => this.light(), 100);
  }

  // Custom pattern for AI response
  static aiResponse(): void {
    this.medium();
  }
}