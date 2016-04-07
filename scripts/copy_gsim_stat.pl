#!/usr/intel/bin/perl5.14.1
use Getopt::Long;
use Cwd 'abs_path';
use File::Basename qw( dirname );
use strict;

print "#\$Header:  2006/05/04 16:10:08 sfu Exp $ \ ";
print "\n\n";

&GetOptions("from_dir=s",
            "to_dir=s",
            "debug");

my $idir = $::opt_from_dir;
my $odir = $::opt_to_dir;

if (-d $odir) {
} else {
    print "$odir does not exist\n";
    exit -1;
}

my $summary = "$idir/data/summary.csv";
my $fh;
open ($fh, $summary) || die "could not open summary file $summary";

my $line = <$fh>;
my @header_list = split /,/, $line;
my $cnt = 0;
my %header;
foreach my $head (@header_list) {
    $header{$head} = $cnt++;
}

while (<$fh>) {
    my @data = split /,/, $_;
    my $cfg  = $data[$header{"level_name"}];
    my $dir  = (split /\//, $cfg)[-1];
    if (-d "$odir/$dir") {
    } else {
        printf ("making directory $odir/$dir\n");
        system ("mkdir $odir/$dir");
    }
    my $src  = $data[$header{"test_dir"}];
    my $src_file = "$idir/tests/$src/psim.stat";
    my $dst = $data[$header{"test_args"}];
    $dst =~ s/\//_/g;
    my $dst_file = "$odir/$dir/$dst.stat";
    if (-f $src_file) {
    } else {
        $src_file .= ".gz";
        $dst_file .= ".gz";
    }
    my $stat = $data[$header{"result"}];
    if ($stat eq "passed" || $stat eq "ran") {
        my $cmd = sprintf("cp %s %s", $src_file, $dst_file);
        print ($cmd, "\n");
        system ($cmd);        
        if ($dst_file =~ /.gz/) {
        } else {
            printf ("gzip %s\n", $dst_file);
        }
    } else {
    }
}
close $fh;

    

