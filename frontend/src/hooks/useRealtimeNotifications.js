import { useEffect, useState } from 'react'
import { supabase } from '../supabaseClient'

/**
 * Hook to subscribe to real-time notifications
 * @param {string} userId - Current user's ID
 * @returns {Array} notifications - Array of new notifications
 */
export function useRealtimeNotifications(userId) {
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    if (!userId) return

    // Subscribe to notifications table changes for this user
    const channel = supabase
      .channel(`notifications-${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          console.log('New notification:', payload.new)
          setNotifications((prev) => [payload.new, ...prev])
          
          // Optional: Show browser notification
          if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(payload.new.title, {
              body: payload.new.message,
              icon: '/logo192.png'
            })
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [userId])

  return notifications
}

/**
 * Hook to subscribe to real-time question updates
 * @returns {Array} newQuestions - Array of new questions
 */
export function useRealtimeQuestions() {
  const [newQuestions, setNewQuestions] = useState([])

  useEffect(() => {
    // Subscribe to new questions
    const channel = supabase
      .channel('public-questions')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'questions'
        },
        (payload) => {
          console.log('New question:', payload.new)
          setNewQuestions((prev) => [payload.new, ...prev])
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  return newQuestions
}

/**
 * Hook to subscribe to answers for a specific question
 * @param {string} questionId - Question ID to subscribe to
 * @returns {Array} newAnswers - Array of new answers
 */
export function useRealtimeAnswers(questionId) {
  const [newAnswers, setNewAnswers] = useState([])

  useEffect(() => {
    if (!questionId) return

    // Subscribe to new answers for this question
    const channel = supabase
      .channel(`answers-${questionId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'answers',
          filter: `question_id=eq.${questionId}`
        },
        (payload) => {
          console.log('New answer:', payload.new)
          setNewAnswers((prev) => [payload.new, ...prev])
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [questionId])

  return newAnswers
}

/**
 * Request browser notification permission
 */
export function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().then((permission) => {
      if (permission === 'granted') {
        console.log('Notification permission granted')
      }
    })
  }
}
