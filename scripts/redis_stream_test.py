#!/usr/bin/env python3
"""
Redis Stream Testing Script
This script provides commands to test the Redis stream performance:
1. Saturation test: Grows tasks in the Redis stream to test system limits
2. Steady-state test: Maintains a constant number of elements without saturation
"""

import time
import uuid
from datetime import datetime
from typing import Optional

import click
import redis

REDIS_STREAM_NAME = 'video_tasks'


def get_redis_client(host: str = 'localhost', port: int = 6379, db: int = 0) -> redis.Redis:
    """Create and return a Redis client connection."""
    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


def generate_task_message(video_id: Optional[str] = None, source_path: Optional[str] = None) -> dict:
    """
    Generate a task message for the Redis stream.
    
    Args:
        video_id: Optional video ID. If not provided, generates a random UUID.
        source_path: Optional source path. If not provided, generates a test path.
    
    Returns:
        A dictionary with task_id, video_id, and source_path.
    """
    task_id = str(uuid.uuid4())
    video_id = video_id or str(uuid.uuid4())
    source_path = source_path or f"test/videos/{video_id}.mp4"
    
    return {
        "task_id": task_id,
        "video_id": video_id,
        "source_path": source_path,
        "attempt": "0"
    }


def get_stream_length(client: redis.Redis, stream_name: str) -> int:
    """Get the current length of a Redis stream."""
    return client.xlen(stream_name)


@click.group()
def cli():
    """Redis Stream Testing Tool for video processing tasks."""
    pass


@cli.command()
@click.option('--host', default='localhost', help='Redis host (default: localhost)')
@click.option('--port', default=6379, help='Redis port (default: 6379)')
@click.option('--rate', default=100, help='Number of tasks to add per second (default: 100)')
@click.option('--duration', default=60, help='Duration of the test in seconds (default: 60)')
@click.option('--target-size', default=10000, help='Target stream size to reach (default: 10000)')
def saturation(host: str, port: int, rate: int, duration: int, target_size: int):
    """
    Saturation Test: Continuously add tasks to the Redis stream to test system limits.
    
    This test will add tasks at the specified rate until either the duration expires
    or the target stream size is reached. The goal is to saturate the system and
    observe how it handles high load.
    
    Examples:
        # Default settings (100 tasks/sec for 60 seconds)
        python redis_stream_test.py saturation
        
        # High load test (500 tasks/sec for 120 seconds)
        python redis_stream_test.py saturation --rate 500 --duration 120
        
        # Reach specific target size
        python redis_stream_test.py saturation --rate 200 --target-size 50000
    """
    click.echo(f"🚀 Starting Saturation Test")
    click.echo(f"   Redis: {host}:{port}")
    click.echo(f"   Rate: {rate} tasks/second")
    click.echo(f"   Duration: {duration} seconds")
    click.echo(f"   Target Size: {target_size} tasks")
    click.echo(f"   Stream: {REDIS_STREAM_NAME}")
    click.echo()
    
    try:
        client = get_redis_client(host, port)
        client.ping()
        click.echo("✓ Connected to Redis")
    except Exception as e:
        click.echo(f"✗ Failed to connect to Redis: {e}", err=True)
        return
    
    start_time = time.time()
    tasks_added = 0
    interval = 1.0 / rate  # Time between each task
    
    initial_size = get_stream_length(client, REDIS_STREAM_NAME)
    click.echo(f"Initial stream size: {initial_size}")
    click.echo()
    
    try:
        while True:
            loop_start = time.time()
            elapsed = loop_start - start_time
            
            # Check exit conditions
            if elapsed >= duration:
                click.echo(f"\n⏱️  Duration reached ({duration}s)")
                break
            
            current_size = get_stream_length(client, REDIS_STREAM_NAME)
            if current_size >= target_size:
                click.echo(f"\n🎯 Target size reached ({current_size} >= {target_size})")
                break
            
            # Add task to stream
            message = generate_task_message()
            client.xadd(REDIS_STREAM_NAME, message)
            tasks_added += 1
            
            # Print progress every second
            if tasks_added % rate == 0:
                current_size = get_stream_length(client, REDIS_STREAM_NAME)
                tasks_per_sec = tasks_added / elapsed if elapsed > 0 else 0
                click.echo(f"[{elapsed:.1f}s] Added: {tasks_added} | Stream size: {current_size} | Rate: {tasks_per_sec:.1f} tasks/s")
            
            # Sleep to maintain rate
            sleep_time = interval - (time.time() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        click.echo(f"\n\n✗ Error during test: {e}", err=True)
    
    # Final statistics
    end_time = time.time()
    total_duration = end_time - start_time
    final_size = get_stream_length(client, REDIS_STREAM_NAME)
    avg_rate = tasks_added / total_duration if total_duration > 0 else 0
    
    click.echo()
    click.echo("=" * 60)
    click.echo("📊 Saturation Test Results")
    click.echo("=" * 60)
    click.echo(f"Total duration:        {total_duration:.2f} seconds")
    click.echo(f"Tasks added:           {tasks_added}")
    click.echo(f"Average rate:          {avg_rate:.2f} tasks/second")
    click.echo(f"Initial stream size:   {initial_size}")
    click.echo(f"Final stream size:     {final_size}")
    click.echo(f"Net growth:            {final_size - initial_size}")
    click.echo("=" * 60)


@cli.command()
@click.option('--host', default='localhost', help='Redis host (default: localhost)')
@click.option('--port', default=6379, help='Redis port (default: 6379)')
@click.option('--target', default=1000, help='Target number of tasks to maintain (default: 1000)')
@click.option('--rate', default=50, help='Number of tasks to add per second (default: 50)')
@click.option('--duration', default=300, help='Duration of the test in seconds (default: 300)')
@click.option('--tolerance', default=0.1, help='Tolerance as percentage (default: 0.1 = 10%)')
def steady_state(host: str, port: int, target: int, rate: int, duration: int, tolerance: float):
    """
    Steady-State Test: Maintain a constant number of elements in the stream.
    
    This test monitors the stream size and adjusts the task injection rate to maintain
    a target number of tasks in the queue. The goal is to match the processing rate
    and keep the system in a stable state without saturation.
    
    Examples:
        # Default settings (maintain 1000 tasks for 300 seconds)
        python redis_stream_test.py steady-state
        
        # Maintain 5000 tasks with 100 tasks/sec base rate
        python redis_stream_test.py steady-state --target 5000 --rate 100
        
        # Short test with tight tolerance
        python redis_stream_test.py steady-state --target 500 --duration 60 --tolerance 0.05
    """
    click.echo(f"⚖️  Starting Steady-State Test")
    click.echo(f"   Redis: {host}:{port}")
    click.echo(f"   Target: {target} tasks")
    click.echo(f"   Base rate: {rate} tasks/second")
    click.echo(f"   Duration: {duration} seconds")
    click.echo(f"   Tolerance: {tolerance * 100}%")
    click.echo(f"   Stream: {REDIS_STREAM_NAME}")
    click.echo()
    
    try:
        client = get_redis_client(host, port)
        client.ping()
        click.echo("✓ Connected to Redis")
    except Exception as e:
        click.echo(f"✗ Failed to connect to Redis: {e}", err=True)
        return
    
    start_time = time.time()
    tasks_added = 0
    interval = 1.0 / rate  # Base interval
    
    initial_size = get_stream_length(client, REDIS_STREAM_NAME)
    click.echo(f"Initial stream size: {initial_size}")
    
    # If initial size is below target, ramp up first
    if initial_size < target:
        click.echo(f"\n📈 Ramping up to target size ({initial_size} → {target})...")
        ramp_up_start = time.time()
        while get_stream_length(client, REDIS_STREAM_NAME) < target:
            message = generate_task_message()
            client.xadd(REDIS_STREAM_NAME, message)
            tasks_added += 1
            if tasks_added % 100 == 0:
                current_size = get_stream_length(client, REDIS_STREAM_NAME)
                click.echo(f"   Ramp up: {current_size}/{target} tasks")
        ramp_up_duration = time.time() - ramp_up_start
        click.echo(f"✓ Reached target in {ramp_up_duration:.2f}s")
    
    click.echo()
    click.echo("🔄 Entering steady-state maintenance phase...")
    click.echo()
    
    # Statistics tracking
    measurements = []
    in_range_count = 0
    out_range_count = 0
    
    lower_bound = target * (1 - tolerance)
    upper_bound = target * (1 + tolerance)
    
    try:
        last_report = time.time()
        report_interval = 5  # Report every 5 seconds
        
        while True:
            loop_start = time.time()
            elapsed = loop_start - start_time
            
            # Check exit condition
            if elapsed >= duration:
                click.echo(f"\n⏱️  Duration reached ({duration}s)")
                break
            
            # Get current stream size
            current_size = get_stream_length(client, REDIS_STREAM_NAME)
            measurements.append(current_size)
            
            # Determine if we're in range
            in_range = lower_bound <= current_size <= upper_bound
            if in_range:
                in_range_count += 1
            else:
                out_range_count += 1
            
            # Adjust injection rate based on current size vs target
            # If size is below target, we need to add more tasks
            # If size is above target, we need to add fewer tasks
            size_ratio = current_size / target if target > 0 else 1.0
            
            # Dynamic rate adjustment: inverse relationship with queue size
            if size_ratio < 0.9:
                # Queue is draining, increase rate significantly
                adjusted_rate = rate * 1.5
            elif size_ratio < 0.95:
                # Queue is slightly below, increase rate moderately
                adjusted_rate = rate * 1.2
            elif size_ratio > 1.1:
                # Queue is growing, decrease rate significantly
                adjusted_rate = rate * 0.5
            elif size_ratio > 1.05:
                # Queue is slightly above, decrease rate moderately
                adjusted_rate = rate * 0.8
            else:
                # In range, use base rate
                adjusted_rate = rate
            
            # Add task if adjusted rate indicates we should
            current_interval = 1.0 / adjusted_rate if adjusted_rate > 0 else interval
            
            # Add task to stream
            message = generate_task_message()
            client.xadd(REDIS_STREAM_NAME, message)
            tasks_added += 1
            
            # Report progress periodically
            if time.time() - last_report >= report_interval:
                status = "✓ IN RANGE" if in_range else "⚠ OUT OF RANGE"
                avg_size = sum(measurements[-100:]) / len(measurements[-100:]) if measurements else 0
                stability = (in_range_count / (in_range_count + out_range_count) * 100) if (in_range_count + out_range_count) > 0 else 0
                
                click.echo(
                    f"[{elapsed:.0f}s] {status} | "
                    f"Size: {current_size} | "
                    f"Target: {target} | "
                    f"Avg: {avg_size:.0f} | "
                    f"Rate: {adjusted_rate:.1f}/s | "
                    f"Stability: {stability:.1f}%"
                )
                last_report = time.time()
            
            # Sleep to maintain rate
            sleep_time = current_interval - (time.time() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        click.echo(f"\n\n✗ Error during test: {e}", err=True)
    
    # Final statistics
    end_time = time.time()
    total_duration = end_time - start_time
    final_size = get_stream_length(client, REDIS_STREAM_NAME)
    
    if measurements:
        avg_size = sum(measurements) / len(measurements)
        min_size = min(measurements)
        max_size = max(measurements)
        std_dev = (sum((x - avg_size) ** 2 for x in measurements) / len(measurements)) ** 0.5
    else:
        avg_size = min_size = max_size = std_dev = 0
    
    stability_percentage = (in_range_count / (in_range_count + out_range_count) * 100) if (in_range_count + out_range_count) > 0 else 0
    
    click.echo()
    click.echo("=" * 60)
    click.echo("📊 Steady-State Test Results")
    click.echo("=" * 60)
    click.echo(f"Total duration:        {total_duration:.2f} seconds")
    click.echo(f"Tasks added:           {tasks_added}")
    click.echo(f"Target size:           {target}")
    click.echo(f"Tolerance range:       {lower_bound:.0f} - {upper_bound:.0f}")
    click.echo()
    click.echo(f"Final size:            {final_size}")
    click.echo(f"Average size:          {avg_size:.2f}")
    click.echo(f"Min size:              {min_size}")
    click.echo(f"Max size:              {max_size}")
    click.echo(f"Std deviation:         {std_dev:.2f}")
    click.echo()
    click.echo(f"In-range measurements: {in_range_count}")
    click.echo(f"Out-range measurements:{out_range_count}")
    click.echo(f"Stability:             {stability_percentage:.2f}%")
    click.echo("=" * 60)
    
    # Performance verdict
    click.echo()
    if stability_percentage >= 90:
        click.echo("✓ EXCELLENT: System maintained steady state very well")
    elif stability_percentage >= 70:
        click.echo("✓ GOOD: System maintained steady state adequately")
    elif stability_percentage >= 50:
        click.echo("⚠ FAIR: System struggled to maintain steady state")
    else:
        click.echo("✗ POOR: System failed to maintain steady state")


@cli.command()
@click.option('--host', default='localhost', help='Redis host (default: localhost)')
@click.option('--port', default=6379, help='Redis port (default: 6379)')
def status(host: str, port: int):
    """
    Show current status of the Redis stream.
    
    Displays information about the current state of the video_tasks stream,
    including length, consumer groups, and pending messages.
    """
    click.echo(f"📊 Redis Stream Status")
    click.echo(f"   Redis: {host}:{port}")
    click.echo(f"   Stream: {REDIS_STREAM_NAME}")
    click.echo()
    
    try:
        client = get_redis_client(host, port)
        client.ping()
        click.echo("✓ Connected to Redis")
        click.echo()
    except Exception as e:
        click.echo(f"✗ Failed to connect to Redis: {e}", err=True)
        return
    
    try:
        # Stream length
        stream_length = get_stream_length(client, REDIS_STREAM_NAME)
        click.echo(f"Stream length: {stream_length} messages")
        
        # Consumer groups info
        try:
            groups = client.xinfo_groups(REDIS_STREAM_NAME)
            if groups:
                click.echo(f"\nConsumer groups: {len(groups)}")
                for group in groups:
                    click.echo(f"  - {group['name']}: {group['pending']} pending, {group['consumers']} consumers")
        except redis.exceptions.ResponseError:
            click.echo("\nNo consumer groups exist yet")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error getting stream info: {e}", err=True)


@cli.command()
@click.option('--host', default='localhost', help='Redis host (default: localhost)')
@click.option('--port', default=6379, help='Redis port (default: 6379)')
@click.confirmation_option(prompt='Are you sure you want to clear the stream?')
def clear(host: str, port: int):
    """
    Clear all messages from the Redis stream.
    
    WARNING: This will delete all messages in the video_tasks stream.
    Use with caution!
    """
    click.echo(f"🗑️  Clearing Redis Stream")
    click.echo(f"   Redis: {host}:{port}")
    click.echo(f"   Stream: {REDIS_STREAM_NAME}")
    click.echo()
    
    try:
        client = get_redis_client(host, port)
        client.ping()
    except Exception as e:
        click.echo(f"✗ Failed to connect to Redis: {e}", err=True)
        return
    
    try:
        initial_length = get_stream_length(client, REDIS_STREAM_NAME)
        client.delete(REDIS_STREAM_NAME)
        click.echo(f"✓ Cleared {initial_length} messages from stream")
    except Exception as e:
        click.echo(f"✗ Error clearing stream: {e}", err=True)


if __name__ == '__main__':
    cli()
