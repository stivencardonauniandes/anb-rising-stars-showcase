#!/usr/bin/env python3
"""
SQS Queue Testing Script
This script provides commands to test the AWS SQS queue performance:
1. Saturation test: Grows tasks in the SQS queue to test system limits
2. Steady-state test: Maintains a constant number of elements without saturation
"""

import json
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Optional

import boto3
import click
from botocore.exceptions import ClientError


def get_sqs_client(region: str = 'us-east-1'):
    """Create and return an SQS client connection."""
    return boto3.client('sqs', region_name=region)


def generate_task_message(video_id: Optional[str] = None, source_path: Optional[str] = None) -> dict:
    """
    Generate a task message for the SQS queue.
    
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


def get_queue_length(client, queue_url: str) -> int:
    """Get the approximate number of messages in an SQS queue."""
    response = client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
    )
    visible = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
    not_visible = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
    return visible + not_visible



@click.group()
def cli():
    """SQS Queue Testing Tool for video processing tasks."""
    pass


@cli.command()
@click.option('--region', default='us-east-1', help='AWS region (default: us-east-1)')
@click.option('--queue-url', required=True, help='SQS queue URL')
@click.option('--rate', default=100, help='Number of tasks to add per second (default: 100, 0 for unlimited)')
@click.option('--duration', default=60, help='Duration of the test in seconds (default: 60, ignored if --manual-stop)')
@click.option('--target-size', default=10000, help='Target queue size to reach (default: 10000, ignored if --manual-stop)')
@click.option('--manual-stop', is_flag=True, help='Run until you press Enter (ignores duration and target-size)')
@click.option('--batch-size', default=10, help='Number of tasks to add per batch (default: 10, higher = faster saturation, max 10 for SQS)')
@click.option('--video-id', default=None, help='Optional video ID (generates random UUID if not provided)')
@click.option('--source-path', default=None, help='Optional source path (generates test path if not provided)')
def saturation(region: str, queue_url: str, rate: int, duration: int, target_size: int, manual_stop: bool, batch_size: int, video_id: str, source_path: str):
    """
    Saturation Test: Continuously add tasks to the SQS queue to test system limits.
    
    This test adds tasks faster than workers can process them, causing the queue to grow.
    Use --rate 0 for unlimited speed (maximum saturation), or set a specific rate.
    The test runs until duration expires, target size is reached, or Enter is pressed (--manual-stop).
    
    Examples:
        # Maximum saturation (no rate limit, manual stop)
        python sqs_queue_test.py saturation --rate 0 --manual-stop
        
        # Controlled saturation (100 tasks/sec for 60 seconds)
        python sqs_queue_test.py saturation --rate 100 --duration 60
        
        # High load test with batching (500 tasks/sec for 120 seconds)
        python sqs_queue_test.py saturation --rate 500 --duration 120 --batch-size 10
        
        # Reach specific target size quickly
        python sqs_queue_test.py saturation --rate 0 --target-size 50000 --batch-size 10
        
        # Manual stop with controlled rate
        python sqs_queue_test.py saturation --rate 200 --manual-stop
    """
    # SQS batch limit is 10
    if batch_size > 10:
        click.echo(f"⚠️  Batch size limited to 10 (SQS maximum). Requested: {batch_size}")
        batch_size = 10
    
    click.echo(f"🚀 Starting Saturation Test")
    click.echo(f"   AWS Region: {region}")
    click.echo(f"   Queue URL: {queue_url}")
    click.echo(f"   Rate: {'UNLIMITED (maximum saturation)' if rate == 0 else f'{rate} tasks/second'}")
    click.echo(f"   Batch Size: {batch_size} tasks per batch")
    if manual_stop:
        click.echo(f"   Mode: Manual stop (press Enter to stop)")
    else:
        click.echo(f"   Duration: {duration} seconds")
        click.echo(f"   Target Size: {target_size} tasks")
    click.echo()
    
    try:
        client = get_sqs_client(region)
        click.echo(f"✓ Connected to SQS")
    except Exception as e:
        click.echo(f"✗ Failed to connect to SQS: {e}", err=True)
        return
    
    start_time = time.time()
    tasks_added = 0
    last_report_time = start_time
    report_interval = 1.0  # Report every second
    
    # Calculate batch timing for rate limiting
    unlimited_rate = (rate == 0)
    if unlimited_rate:
        batch_interval = 0  # No delay between batches
    else:
        batch_interval = batch_size / rate  # Time to wait between batches
    
    initial_size = get_queue_length(client, queue_url)
    click.echo(f"Initial queue size: {initial_size}")
    
    if manual_stop:
        click.echo()
        click.echo("⚠️  Press ENTER at any time to stop the test...")
        click.echo()
    else:
        click.echo()
    
    # For manual stop mode, use a flag that will be set when Enter is pressed
    stop_flag = threading.Event()
    
    def wait_for_enter():
        """Thread function to wait for Enter key press"""
        input()
        stop_flag.set()
    
    # Start the input thread if in manual stop mode
    if manual_stop:
        input_thread = threading.Thread(target=wait_for_enter, daemon=True)
        input_thread.start()
    
    try:
        while True:
            batch_start = time.time()
            elapsed = batch_start - start_time
            
            # Check exit conditions
            if manual_stop:
                # In manual mode, only stop when Enter is pressed
                if stop_flag.is_set():
                    click.echo(f"\n✋ Manually stopped by user")
                    break
            else:
                # In automatic mode, check duration and target size
                if elapsed >= duration:
                    click.echo(f"\n⏱️  Duration reached ({duration}s)")
                    break
                
                current_size = get_queue_length(client, queue_url)
                if current_size >= target_size:
                    click.echo(f"\n🎯 Target size reached ({current_size} >= {target_size})")
                    break
            
            # Add batch of tasks to queue
            entries = []
            for i in range(batch_size):
                message = generate_task_message(video_id, source_path)
                entries.append({
                    'Id': str(i),
                    'MessageBody': json.dumps(message)
                })
            
            client.send_message_batch(QueueUrl=queue_url, Entries=entries)
            tasks_added += batch_size
            
            # Print progress report every second
            current_time = time.time()
            if current_time - last_report_time >= report_interval:
                current_size = get_queue_length(client, queue_url)
                elapsed_total = current_time - start_time
                tasks_per_sec = tasks_added / elapsed_total if elapsed_total > 0 else 0
                growth_rate = (current_size - initial_size) / elapsed_total if elapsed_total > 0 else 0
                click.echo(
                    f"[{elapsed_total:.1f}s] Added: {tasks_added} | "
                    f"Queue size: {current_size} (+{current_size - initial_size}) | "
                    f"Add rate: {tasks_per_sec:.1f}/s | "
                    f"Growth: {growth_rate:.1f}/s"
                )
                last_report_time = current_time
            
            # Sleep to maintain rate (if not unlimited)
            if not unlimited_rate and batch_interval > 0:
                sleep_time = batch_interval - (time.time() - batch_start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Test interrupted by user (Ctrl+C)")
    except Exception as e:
        click.echo(f"\n\n✗ Error during test: {e}", err=True)
    
    # Final statistics
    end_time = time.time()
    total_duration = end_time - start_time
    final_size = get_queue_length(client, queue_url)
    avg_rate = tasks_added / total_duration if total_duration > 0 else 0
    
    click.echo()
    click.echo("=" * 60)
    click.echo("📊 Saturation Test Results")
    click.echo("=" * 60)
    click.echo(f"Total duration:        {total_duration:.2f} seconds")
    click.echo(f"Tasks added:           {tasks_added}")
    click.echo(f"Average rate:          {avg_rate:.2f} tasks/second")
    click.echo(f"Initial queue size:    {initial_size}")
    click.echo(f"Final queue size:      {final_size}")
    click.echo(f"Net growth:            {final_size - initial_size}")
    click.echo("=" * 60)



@cli.command()
@click.option('--region', default='us-east-1', help='AWS region (default: us-east-1)')
@click.option('--queue-url', required=True, help='SQS queue URL')
@click.option('--target', default=1000, help='Target number of tasks to maintain (default: 1000)')
@click.option('--rate', default=50, help='Number of tasks to add per second (default: 50)')
@click.option('--duration', default=300, help='Duration of the test in seconds (default: 300)')
@click.option('--tolerance', default=0.1, help='Tolerance as percentage (default: 0.1 = 10%)')
@click.option('--video-id', default=None, help='Optional video ID (generates random UUID if not provided)')
@click.option('--source-path', default=None, help='Optional source path (generates test path if not provided)')
def steady_state(region: str, queue_url: str, target: int, rate: int, duration: int, tolerance: float, video_id: str, source_path: str):
    """
    Steady-State Test: Maintain a constant number of elements in the queue.
    
    This test monitors the queue size and adjusts the task injection rate to maintain
    a target number of tasks in the queue. The goal is to match the processing rate
    and keep the system in a stable state without saturation.
    
    Examples:
        # Default settings (maintain 1000 tasks for 300 seconds)
        python sqs_queue_test.py steady-state
        
        # Maintain 5000 tasks with 100 tasks/sec base rate
        python sqs_queue_test.py steady-state --target 5000 --rate 100
        
        # Short test with tight tolerance
        python sqs_queue_test.py steady-state --target 500 --duration 60 --tolerance 0.05
    """
    click.echo(f"⚖️  Starting Steady-State Test")
    click.echo(f"   AWS Region: {region}")
    click.echo(f"   Queue URL: {queue_url}")
    click.echo(f"   Target: {target} tasks")
    click.echo(f"   Base rate: {rate} tasks/second")
    click.echo(f"   Duration: {duration} seconds")
    click.echo(f"   Tolerance: {tolerance * 100}%")
    click.echo()
    
    try:
        client = get_sqs_client(region)
        click.echo(f"✓ Connected to SQS")
    except Exception as e:
        click.echo(f"✗ Failed to connect to SQS: {e}", err=True)
        return
    
    start_time = time.time()
    tasks_added = 0
    interval = 1.0 / rate  # Base interval
    
    initial_size = get_queue_length(client, queue_url)
    click.echo(f"Initial queue size: {initial_size}")
    
    # If initial size is below target, ramp up first
    if initial_size < target:
        click.echo(f"\n📈 Ramping up to target size ({initial_size} → {target})...")
        ramp_up_start = time.time()
        while get_queue_length(client, queue_url) < target:
            message = generate_task_message(video_id, source_path)
            client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
            tasks_added += 1
            if tasks_added % 100 == 0:
                current_size = get_queue_length(client, queue_url)
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
            
            # Get current queue size
            current_size = get_queue_length(client, queue_url)
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
            
            # Add task to queue
            message = generate_task_message(video_id, source_path)
            client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
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
    final_size = get_queue_length(client, queue_url)
    
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
@click.option('--region', default='us-east-1', help='AWS region (default: us-east-1)')
@click.option('--queue-url', required=True, help='SQS queue URL')
def status(region: str, queue_url: str):
    """
    Show current status of the SQS queue.
    
    Displays information about the current state of the video_tasks queue,
    including approximate message counts and queue attributes.
    """
    click.echo(f"📊 SQS Queue Status")
    click.echo(f"   AWS Region: {region}")
    click.echo(f"   Queue URL: {queue_url}")
    click.echo()
    
    try:
        client = get_sqs_client(region)
        click.echo(f"✓ Connected to SQS")
        click.echo()
    except Exception as e:
        click.echo(f"✗ Failed to connect to SQS: {e}", err=True)
        return
    
    try:
        # Get queue attributes
        response = client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
                'ApproximateNumberOfMessagesDelayed',
                'CreatedTimestamp',
                'LastModifiedTimestamp',
                'VisibilityTimeout',
                'MessageRetentionPeriod',
                'ReceiveMessageWaitTimeSeconds'
            ]
        )
        
        attrs = response['Attributes']
        visible = int(attrs.get('ApproximateNumberOfMessages', 0))
        not_visible = int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0))
        delayed = int(attrs.get('ApproximateNumberOfMessagesDelayed', 0))
        total = visible + not_visible + delayed
        
        click.echo(f"Message counts (approximate):")
        click.echo(f"  Available messages:        {visible}")
        click.echo(f"  In-flight messages:        {not_visible}")
        click.echo(f"  Delayed messages:          {delayed}")
        click.echo(f"  Total messages:            {total}")
        click.echo()
        
        click.echo(f"Queue settings:")
        click.echo(f"  Visibility timeout:        {attrs.get('VisibilityTimeout', 'N/A')} seconds")
        click.echo(f"  Message retention:         {int(attrs.get('MessageRetentionPeriod', 0)) // 86400} days")
        click.echo(f"  Receive wait time:         {attrs.get('ReceiveMessageWaitTimeSeconds', 'N/A')} seconds")
        
        created = datetime.fromtimestamp(int(attrs.get('CreatedTimestamp', 0)))
        modified = datetime.fromtimestamp(int(attrs.get('LastModifiedTimestamp', 0)))
        click.echo(f"  Created:                   {created}")
        click.echo(f"  Last modified:             {modified}")
        click.echo()
        
    except Exception as e:
        click.echo(f"✗ Error getting queue info: {e}", err=True)


@cli.command()
@click.option('--region', default='us-east-1', help='AWS region (default: us-east-1)')
@click.option('--queue-url', required=True, help='SQS queue URL')
@click.option('--video-id', default=None, help='Optional video ID (generates random UUID if not provided)')
@click.option('--source-path', default=None, help='Optional source path (generates test path if not provided)')
def add_task(region: str, queue_url: str, video_id: str, source_path: str):
    """
    Add a single task to the SQS queue.
    
    This is useful for testing basic connectivity and worker processing,
    or for manually adding specific tasks to the queue.
    
    Examples:
        # Add a single test task
        python sqs_queue_test.py add-task
        
        # Add task with specific video ID
        python sqs_queue_test.py add-task --video-id "12345-67890"
        
        # Add task with custom source path
        python sqs_queue_test.py add-task --source-path "uploads/my-video.mp4"
    """
    click.echo(f"➕ Adding Single Task to SQS Queue")
    click.echo(f"   AWS Region: {region}")
    click.echo(f"   Queue URL: {queue_url}")
    click.echo()
    
    try:
        client = get_sqs_client(region)
        click.echo(f"✓ Connected to SQS")
    except Exception as e:
        click.echo(f"✗ Failed to connect to SQS: {e}", err=True)
        return
    
    try:
        # Get initial queue size
        initial_size = get_queue_length(client, queue_url)
        
        # Generate and add the task
        message = generate_task_message(video_id, source_path)
        response = client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        # Get new queue size
        new_size = get_queue_length(client, queue_url)
        
        click.echo()
        click.echo("✓ Task added successfully")
        click.echo(f"   Message ID: {response['MessageId']}")
        click.echo(f"   Task ID: {message['task_id']}")
        click.echo(f"   Video ID: {message['video_id']}")
        click.echo(f"   Source Path: {message['source_path']}")
        click.echo()
        click.echo(f"Queue size: {initial_size} → {new_size}")
        
    except Exception as e:
        click.echo(f"✗ Error adding task: {e}", err=True)


@cli.command()
@click.option('--region', default='us-east-1', help='AWS region (default: us-east-1)')
@click.option('--queue-url', required=True, help='SQS queue URL')
@click.confirmation_option(prompt='Are you sure you want to purge the queue?')
def clear(region: str, queue_url: str):
    """
    Purge all messages from the SQS queue.
    
    WARNING: This will delete all messages in the video_tasks queue.
    Purged messages cannot be recovered. Use with caution!
    
    Note: After purging, you must wait 60 seconds before purging again.
    """
    click.echo(f"🗑️  Purging SQS Queue")
    click.echo(f"   AWS Region: {region}")
    click.echo(f"   Queue URL: {queue_url}")
    click.echo()
    
    try:
        client = get_sqs_client(region)
    except Exception as e:
        click.echo(f"✗ Failed to connect to SQS: {e}", err=True)
        return
    
    try:
        initial_length = get_queue_length(client, queue_url)
        
        # Purge the queue
        client.purge_queue(QueueUrl=queue_url)
        click.echo(f"✓ Queue purge initiated ({initial_length} messages will be deleted)")
        click.echo(f"⏳ Purge may take up to 60 seconds to complete")
        click.echo(f"⚠️  You must wait 60 seconds before purging this queue again")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'PurgeQueueInProgress':
            click.echo(f"✗ Purge already in progress. Wait 60 seconds before trying again.", err=True)
        else:
            click.echo(f"✗ Error purging queue: {e}", err=True)
    except Exception as e:
        click.echo(f"✗ Error purging queue: {e}", err=True)
