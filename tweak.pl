#!/usr/bin/perl
use strict;
use warnings;

# Hash to store current sysctl settings with options for performance and secure defaults
my %settings = (
    'hw.smt' => {
        'desc'       => 'Enable Simultaneous Multi-Threading (SMT)',
        'value'      => `sysctl -n hw.smt` // 0,
        'performance' => 1,
        'secure'     => 0,
        'warning'    => 'Enabling SMT may lower security on multi-user systems.',
    },
    'kern.maxfiles' => {
        'desc'       => 'Maximum number of open files',
        'value'      => `sysctl -n kern.maxfiles` // 65536,
        'performance' => 65536,
        'secure'     => 1024,
        'warning'    => '',
    },
    'kern.somaxconn' => {
        'desc'       => 'Maximum number of socket connections',
        'value'      => `sysctl -n kern.somaxconn` // 1024,
        'performance' => 1024,
        'secure'     => 128,
        'warning'    => '',
    },
    'net.inet.ip.ifq.maxlen' => {
        'desc'       => 'Maximum packet queue length',
        'value'      => `sysctl -n net.inet.ip.ifq.maxlen` // 256,
        'performance' => 1024,
        'secure'     => 256,
        'warning'    => '',
    },
);

# Function to update sysctl setting
sub update_sysctl {
    my ($setting, $new_value) = @_;
    print "Setting $setting to $new_value\n"; # For debugging, show what would be set
    system("sysctl $setting=$new_value") == 0
      or warn "Error updating $setting: $!";
}

# Display setting details and allow user to modify
foreach my $setting (keys %settings) {
    my $setting_info = $settings{$setting};

    my $desc        = $setting_info->{'desc'};
    my $current     = $setting_info->{'value'};
    my $performance = $setting_info->{'performance'};
    my $secure      = $setting_info->{'secure'};
    my $warning     = $setting_info->{'warning'};

    print "\nSetting: $setting\n";
    print "$desc\n";
    print "Current: $current\n";
    print "Performance: $performance\n";
    print "Secure Default: $secure\n";
    print "Warning: $warning\n" if $warning;

    print "\nChoose an option:\n";
    print "1. Keep Current ($current)\n";
    print "2. Set for Performance ($performance)\n";
    print "3. Set to Secure Default ($secure)\n";
    print "Enter choice (1-3): ";

    my $choice = <STDIN>;
    chomp $choice;

    if ($choice == 2) {
        update_sysctl($setting, $performance);
    } elsif ($choice == 3) {
        update_sysctl($setting, $secure);
    } else {
        print "No change made to $setting.\n";
    }
}

print "\nScript completed.\n";
